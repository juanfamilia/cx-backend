"""Readiness Gate — política, signatarios, firmas y transición a ``approved``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_instrument_qa_run_model import FieldInstrumentQARun
from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic
from app.models.field_readiness_model import (
    CompanyFieldReadinessPolicy,
    FieldReadinessPolicyPublic,
    FieldReadinessPolicyUpsert,
    FieldReadinessSignature,
    FieldReadinessSignaturePublic,
    FieldReadinessSignatory,
    FieldReadinessSignatoryCreate,
    FieldReadinessSignatoryPublic,
    ReadinessGatePublic,
    ReadinessSignBody,
    ReadinessSignResult,
)
from app.models.user_model import User
from app.services.field_instrument_revision_services import (
    _effective_company_id,
    _get_revision_writable,
)
from app.services.field_readiness_evaluator import (
    READINESS_SIGNATURE_ROLES,
    QARunGateSnapshot,
    ReadinessPolicyView,
    RevisionGateSnapshot,
    evaluate_readiness_gates,
)
from app.services.field_study_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _assert_policy_admin(user: User, company_id: int) -> None:
    if user.role == 0:
        return
    if user.role == 1 and user.company_id == company_id:
        return
    raise PermissionDeniedException(
        custom_message="solo superadmin o gerente de la empresa pueden gestionar política Readiness",
    )


def _policy_row_to_view(row: CompanyFieldReadinessPolicy) -> ReadinessPolicyView:
    return ReadinessPolicyView(
        require_role_research=row.require_role_research,
        require_role_qa=row.require_role_qa,
        require_role_account=row.require_role_account,
        block_on_schema_invalid=row.block_on_schema_invalid,
        block_on_missing_schema_validation=row.block_on_missing_schema_validation,
        block_on_qa_stop=row.block_on_qa_stop,
        block_on_qa_fix_now=row.block_on_qa_fix_now,
        require_qa_run=row.require_qa_run,
        enforce_signatory_grants=row.enforce_signatory_grants,
    )


def _policy_row_to_public(row: CompanyFieldReadinessPolicy) -> FieldReadinessPolicyPublic:
    return FieldReadinessPolicyPublic(
        company_id=row.company_id,
        require_role_research=row.require_role_research,
        require_role_qa=row.require_role_qa,
        require_role_account=row.require_role_account,
        block_on_schema_invalid=row.block_on_schema_invalid,
        block_on_missing_schema_validation=row.block_on_missing_schema_validation,
        block_on_qa_stop=row.block_on_qa_stop,
        block_on_qa_fix_now=row.block_on_qa_fix_now,
        require_qa_run=row.require_qa_run,
        enforce_signatory_grants=row.enforce_signatory_grants,
    )


def _default_policy_public(company_id: int) -> FieldReadinessPolicyPublic:
    return FieldReadinessPolicyPublic(
        company_id=company_id,
        require_role_research=True,
        require_role_qa=True,
        require_role_account=False,
        block_on_schema_invalid=True,
        block_on_missing_schema_validation=True,
        block_on_qa_stop=True,
        block_on_qa_fix_now=False,
        require_qa_run=True,
        enforce_signatory_grants=False,
    )


async def get_readiness_policy_public(
    session: AsyncSession,
    company_id: int,
) -> FieldReadinessPolicyPublic:
    row = await session.get(CompanyFieldReadinessPolicy, company_id)
    if row is None:
        return _default_policy_public(company_id)
    return _policy_row_to_public(row)


async def upsert_company_readiness_policy(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    body: FieldReadinessPolicyUpsert,
) -> FieldReadinessPolicyPublic:
    cid = _effective_company_id(user, company_id)
    _assert_policy_admin(user, cid)
    row = await session.get(CompanyFieldReadinessPolicy, cid)
    if row is None:
        base = _default_policy_public(cid)
        row = CompanyFieldReadinessPolicy(
            company_id=cid,
            require_role_research=base.require_role_research,
            require_role_qa=base.require_role_qa,
            require_role_account=base.require_role_account,
            block_on_schema_invalid=base.block_on_schema_invalid,
            block_on_missing_schema_validation=base.block_on_missing_schema_validation,
            block_on_qa_stop=base.block_on_qa_stop,
            block_on_qa_fix_now=base.block_on_qa_fix_now,
            require_qa_run=base.require_qa_run,
            enforce_signatory_grants=base.enforce_signatory_grants,
            updated_by_user_id=user.id,
        )
        session.add(row)

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_user_id = user.id

    await session.commit()
    await session.refresh(row)
    return _policy_row_to_public(row)


async def list_readiness_signatories(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
) -> list[FieldReadinessSignatoryPublic]:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    stmt = (
        select(FieldReadinessSignatory)
        .where(
            FieldReadinessSignatory.company_id == cid,
            FieldReadinessSignatory.deleted_at.is_(None),
        )
        .order_by(FieldReadinessSignatory.id.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldReadinessSignatoryPublic.model_validate(r) for r in rows]


async def create_readiness_signatory(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    body: FieldReadinessSignatoryCreate,
) -> FieldReadinessSignatoryPublic:
    cid = _effective_company_id(user, company_id)
    _assert_policy_admin(user, cid)
    role = body.signature_role.strip()
    if role not in READINESS_SIGNATURE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"signature_role debe ser uno de: {', '.join(sorted(READINESS_SIGNATURE_ROLES))}",
        )
    row = FieldReadinessSignatory(
        company_id=cid,
        user_id=body.user_id,
        signature_role=role,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="signatario duplicado para ese rol y usuario",
        ) from None
    await session.refresh(row)
    return FieldReadinessSignatoryPublic.model_validate(row)


async def soft_delete_readiness_signatory(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    signatory_id: int,
) -> None:
    cid = _effective_company_id(user, company_id)
    _assert_policy_admin(user, cid)
    row = await session.get(FieldReadinessSignatory, signatory_id)
    if row is None or row.company_id != cid or row.deleted_at is not None:
        raise NotFoundException("Signatario no encontrado")
    row.deleted_at = _now_naive_utc()
    await session.commit()


async def _latest_qa_run(
    session: AsyncSession,
    revision_id: int,
    company_id: int,
) -> FieldInstrumentQARun | None:
    stmt = (
        select(FieldInstrumentQARun)
        .where(
            FieldInstrumentQARun.revision_id == revision_id,
            FieldInstrumentQARun.company_id == company_id,
        )
        .order_by(FieldInstrumentQARun.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def _active_signatures_map(
    session: AsyncSession,
    revision_id: int,
    company_id: int,
) -> dict[str, tuple[str, int | None]]:
    stmt = select(FieldReadinessSignature).where(
        FieldReadinessSignature.revision_id == revision_id,
        FieldReadinessSignature.company_id == company_id,
        FieldReadinessSignature.revoked_at.is_(None),
    )
    rows = (await session.execute(stmt)).scalars().all()
    return {r.signature_role: (r.snapshot_spec_hash, r.snapshot_qa_run_id) for r in rows if r.signature_role}


async def _signatory_matrix(
    session: AsyncSession,
    company_id: int,
) -> dict[str, frozenset[int]]:
    stmt = select(FieldReadinessSignatory).where(
        FieldReadinessSignatory.company_id == company_id,
        FieldReadinessSignatory.deleted_at.is_(None),
    )
    rows = (await session.execute(stmt)).scalars().all()
    acc: dict[str, set[int]] = {}
    for r in rows:
        acc.setdefault(r.signature_role, set()).add(r.user_id)
    return {k: frozenset(v) for k, v in acc.items()}


async def _signature_rows_public(
    session: AsyncSession,
    revision_id: int,
    company_id: int,
) -> list[FieldReadinessSignaturePublic]:
    stmt = (
        select(FieldReadinessSignature)
        .where(
            FieldReadinessSignature.revision_id == revision_id,
            FieldReadinessSignature.company_id == company_id,
            FieldReadinessSignature.revoked_at.is_(None),
        )
        .order_by(FieldReadinessSignature.signed_at.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldReadinessSignaturePublic.model_validate(r) for r in rows]


async def build_readiness_gate(
    session: AsyncSession,
    rev_row: object,
    *,
    policy_public: FieldReadinessPolicyPublic,
    policy_view: ReadinessPolicyView,
) -> ReadinessGatePublic:
    cid = rev_row.company_id
    rid = rev_row.id

    qa_run = await _latest_qa_run(session, rid, cid)
    qa_snap = QARunGateSnapshot(
        run_id=qa_run.id if qa_run else None,
        stop_count=qa_run.stop_count if qa_run else 0,
        fix_now_count=qa_run.fix_now_count if qa_run else 0,
    )

    active_sig = await _active_signatures_map(session, rid, cid)
    matrix = await _signatory_matrix(session, cid) if policy_view.enforce_signatory_grants else None

    rev_snap = RevisionGateSnapshot(
        status=rev_row.status,
        content_hash=rev_row.content_hash or "",
        last_validation_ok=rev_row.last_validation_ok,
        last_validation_content_hash=rev_row.last_validation_content_hash,
    )

    ev = evaluate_readiness_gates(
        policy=policy_view,
        revision=rev_snap,
        qa=qa_snap,
        active_signatures=active_sig,
        signatory_user_ids_by_role=matrix,
    )

    sig_pub = await _signature_rows_public(session, rid, cid)

    if rev_row.status == "approved":
        agg = "approved"
    elif ev.blocked:
        agg = "blocked"
    elif len(ev.missing_roles) > 0:
        agg = "pending_signatures"
    elif ev.ready:
        agg = "ready"
    else:
        agg = "blocked"

    return ReadinessGatePublic(
        revision_id=rid,
        revision_status=rev_row.status,
        aggregate_status=agg,
        blocking_codes=list(ev.blocking_codes),
        missing_roles=list(ev.missing_roles),
        stale_roles=list(ev.stale_roles),
        required_roles=list(ev.required_roles),
        policy=policy_public,
        last_validation_ok=rev_row.last_validation_ok,
        content_hash=rev_row.content_hash or "",
        latest_qa_run_id=qa_snap.run_id,
        qa_stop_count=qa_snap.stop_count,
        qa_fix_now_count=qa_snap.fix_now_count,
        signatures=sig_pub,
    )


async def get_readiness_for_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
) -> ReadinessGatePublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    rev = await _get_revision_writable(session, revision_id, cid)

    policy_row = await session.get(CompanyFieldReadinessPolicy, cid)
    policy_public = (
        _policy_row_to_public(policy_row)
        if policy_row is not None
        else _default_policy_public(cid)
    )
    policy_view = (
        _policy_row_to_view(policy_row)
        if policy_row is not None
        else ReadinessPolicyView(
            require_role_research=True,
            require_role_qa=True,
            require_role_account=False,
            block_on_schema_invalid=True,
            block_on_missing_schema_validation=True,
            block_on_qa_stop=True,
            block_on_qa_fix_now=False,
            require_qa_run=True,
            enforce_signatory_grants=False,
        )
    )

    return await build_readiness_gate(session, rev, policy_public=policy_public, policy_view=policy_view)


async def sign_readiness_for_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    body: ReadinessSignBody,
    company_id: Optional[int],
) -> ReadinessSignResult:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    rev = await _get_revision_writable(session, revision_id, cid)

    if rev.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="solo revisiones en borrador admiten firmas Readiness",
        )

    role = body.signature_role.strip()
    if role not in READINESS_SIGNATURE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"signature_role debe ser uno de: {', '.join(sorted(READINESS_SIGNATURE_ROLES))}",
        )

    policy_row = await session.get(CompanyFieldReadinessPolicy, cid)
    policy_public = (
        _policy_row_to_public(policy_row)
        if policy_row is not None
        else _default_policy_public(cid)
    )
    policy_view = (
        _policy_row_to_view(policy_row)
        if policy_row is not None
        else ReadinessPolicyView(
            require_role_research=True,
            require_role_qa=True,
            require_role_account=False,
            block_on_schema_invalid=True,
            block_on_missing_schema_validation=True,
            block_on_qa_stop=True,
            block_on_qa_fix_now=False,
            require_qa_run=True,
            enforce_signatory_grants=False,
        )
    )

    gate_before = await build_readiness_gate(session, rev, policy_public=policy_public, policy_view=policy_view)
    if gate_before.aggregate_status == "blocked":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Readiness bloqueado por políticas o calidad previa a firmar",
                "blocking_codes": gate_before.blocking_codes,
            },
        )

    if role not in gate_before.missing_roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este rol ya está cubierto por una firma vigente o no es requerido por la política",
        )

    if policy_view.enforce_signatory_grants:
        matrix = await _signatory_matrix(session, cid)
        allowed = matrix.get(role, frozenset())
        if user.id not in allowed:
            raise PermissionDeniedException(
                custom_message="usuario no autorizado como signatario para este rol",
            )

    qa_run = await _latest_qa_run(session, revision_id, cid)

    now = _now_naive_utc()
    await session.execute(
        update(FieldReadinessSignature)
        .where(
            FieldReadinessSignature.revision_id == revision_id,
            FieldReadinessSignature.signature_role == role,
            FieldReadinessSignature.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    snap_qa_id = qa_run.id if qa_run else None
    sig_row = FieldReadinessSignature(
        revision_id=revision_id,
        company_id=cid,
        signature_role=role,
        signer_user_id=user.id,
        comment=(body.comment or "").strip() or None,
        snapshot_spec_hash=rev.content_hash or "",
        snapshot_qa_run_id=snap_qa_id,
        signed_at=now,
    )
    session.add(sig_row)

    await session.commit()
    await session.refresh(rev)
    await session.refresh(sig_row)

    gate_after = await build_readiness_gate(session, rev, policy_public=policy_public, policy_view=policy_view)

    if gate_after.aggregate_status == "ready" and rev.status == "draft":
        rev.status = "approved"
        rev.updated_by_user_id = user.id
        await session.commit()
        await session.refresh(rev)

    gate_final = await build_readiness_gate(session, rev, policy_public=policy_public, policy_view=policy_view)

    return ReadinessSignResult(
        readiness=gate_final,
        revision=FieldInstrumentRevisionPublic.model_validate(rev),
    )


async def get_readiness_policy_for_reader(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
) -> FieldReadinessPolicyPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    return await get_readiness_policy_public(session, cid)
