"""Lectura y escritura de la capa de decisión Field (fuentes, políticas, snapshot, sync, hallazgos)."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_decision_model import (
    DoobloAnalysisRequest,
    FieldOperationalSnapshot,
    FieldOperationalSnapshotPublic,
    FieldPolicySet,
    FieldPolicySetCreate,
    FieldPolicySetPublic,
    FieldProjectExternalSource,
    FieldProjectExternalSourceCreate,
    FieldProjectExternalSourcePublic,
    FieldSyncRun,
    FieldSyncRunPublic,
    RUN_KIND_FIELD_ANALYSIS,
    SOURCE_TYPE_CSV,
    SOURCE_TYPE_DOOBLO,
    SOURCE_TYPE_MANUAL,
    SOURCE_TYPE_QUALTRICS,
    SYNC_STRATEGY_FULL,
    SYNC_STRATEGY_INCREMENTAL,
    FieldFindingApprovalBody,
    SYNC_RUN_PENDING,
)
from app.models.field_ledger_model import (
    FieldFinding,
    FieldFindingDecisionLog,
    FieldFindingDecisionLogPublic,
    FieldFindingPublic,
)
from app.models.field_project_model import FieldProject
from app.models.user_model import User
from app.services.field_project_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException

_VALID_SOURCE = frozenset(
    {SOURCE_TYPE_DOOBLO, SOURCE_TYPE_QUALTRICS, SOURCE_TYPE_CSV, SOURCE_TYPE_MANUAL, "api"}
)
_VALID_SYNC = frozenset({SYNC_STRATEGY_FULL, SYNC_STRATEGY_INCREMENTAL, "none"})


def _user_display_name(u: User) -> str:
    name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
    if name:
        return name
    return str(u.email) if u.email else f"user #{u.id}"


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _assert_project_access(user: User, project: FieldProject) -> None:
    if user.role == 0:
        return
    if user.company_id is None or project.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="proyecto Field no permitido")


async def _get_project(session: AsyncSession, project_id: int) -> FieldProject:
    row = await session.get(FieldProject, project_id)
    if row is None or row.deleted_at is not None:
        raise NotFoundException("Proyecto Field no encontrado")
    return row


# --- lectura ---


async def list_external_sources(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldProjectExternalSourcePublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    stmt = (
        select(FieldProjectExternalSource)
        .where(FieldProjectExternalSource.field_project_id == project_id)
        .order_by(FieldProjectExternalSource.id)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldProjectExternalSourcePublic.model_validate(r) for r in rows]


async def list_policy_sets(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldPolicySetPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    stmt = (
        select(FieldPolicySet)
        .where(FieldPolicySet.field_project_id == project_id)
        .order_by(FieldPolicySet.version.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldPolicySetPublic.model_validate(r) for r in rows]


async def get_operational_snapshot(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> FieldOperationalSnapshotPublic | None:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    row = (
        await session.execute(
            select(FieldOperationalSnapshot).where(
                FieldOperationalSnapshot.field_project_id == project_id
            )
        )
    ).scalars().first()
    if row is None:
        return None
    return FieldOperationalSnapshotPublic.model_validate(row)


async def list_sync_runs(
    session: AsyncSession,
    user: User,
    project_id: int,
    limit: int = 30,
) -> list[FieldSyncRunPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    limit = min(max(limit, 1), 200)
    stmt = (
        select(FieldSyncRun)
        .where(FieldSyncRun.field_project_id == project_id)
        .order_by(FieldSyncRun.id.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldSyncRunPublic.model_validate(r) for r in rows]


async def list_project_findings(
    session: AsyncSession,
    user: User,
    project_id: int,
    source: str | None = None,
    limit: int = 200,
) -> list[FieldFindingPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    limit = min(max(limit, 1), 500)
    stmt = select(FieldFinding).where(FieldFinding.field_project_id == project_id)
    if source is not None:
        stmt = stmt.where(FieldFinding.source == source)
    stmt = stmt.order_by(FieldFinding.id.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldFindingPublic.model_validate(r) for r in rows]


async def list_finding_decision_log(
    session: AsyncSession,
    user: User,
    project_id: int,
    finding_id: int,
    limit: int = 100,
) -> list[FieldFindingDecisionLogPublic]:
    """Historial auditable de cambios de estado (aprobación) sobre un hallazgo."""
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    f = await session.get(FieldFinding, finding_id)
    if f is None or f.field_project_id != project_id:
        raise NotFoundException("Hallazgo no encontrado en este proyecto.")
    limit = min(max(limit, 1), 500)
    stmt = (
        select(FieldFindingDecisionLog)
        .where(
            FieldFindingDecisionLog.field_finding_id == finding_id,
            FieldFindingDecisionLog.field_project_id == project_id,
        )
        .order_by(FieldFindingDecisionLog.id.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    if not rows:
        return []
    actor_ids = {r.actor_user_id for r in rows}
    ures = await session.execute(select(User).where(User.id.in_(actor_ids)))
    umap = {u.id: _user_display_name(u) for u in ures.scalars().all()}
    out: list[FieldFindingDecisionLogPublic] = []
    for r in rows:
        base = FieldFindingDecisionLogPublic.model_validate(r)
        out.append(base.model_copy(update={"actor_display": umap.get(r.actor_user_id)}))
    return out


# --- escritura ---


async def create_external_source(
    session: AsyncSession,
    user: User,
    project_id: int,
    body: FieldProjectExternalSourceCreate,
) -> FieldProjectExternalSourcePublic:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    st = (body.source_type or "").strip().lower()
    if st not in _VALID_SOURCE:
        raise HTTPException(
            400, detail=f"source_type no válido. Use: {', '.join(sorted(_VALID_SOURCE))}."
        )
    sync = (body.sync_strategy or None)
    if sync is not None and sync not in (SYNC_STRATEGY_FULL, SYNC_STRATEGY_INCREMENTAL, "none"):
        raise HTTPException(400, detail="sync_strategy debe ser full, incremental, none o null.")

    row = FieldProjectExternalSource(
        field_project_id=project_id,
        company_id=project.company_id,
        source_type=st,
        external_project_id=(body.external_project_id or None),
        external_survey_id=(body.external_survey_id or None),
        external_customer_id=(body.external_customer_id or None),
        wave_id=(body.wave_id or None),
        is_active=body.is_active,
        sync_strategy=None if not sync or sync == "none" else sync,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FieldProjectExternalSourcePublic.model_validate(row)


async def create_policy_set(
    session: AsyncSession,
    user: User,
    project_id: int,
    body: FieldPolicySetCreate,
) -> FieldPolicySetPublic:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)

    res = await session.execute(
        select(func.coalesce(func.max(FieldPolicySet.version), 0)).where(
            FieldPolicySet.field_project_id == project_id
        )
    )
    next_v = int(res.scalar_one() or 0) + 1

    row = FieldPolicySet(
        field_project_id=project_id,
        version=next_v,
        name=(body.name or None),
        config=body.config if body.config is not None else {},
        created_by_user_id=user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FieldPolicySetPublic.model_validate(row)


async def create_sync_run_for_dooblo_analysis(
    session: AsyncSession,
    user: User,
    project_id: int,
    body: DoobloAnalysisRequest,
) -> tuple[FieldSyncRunPublic, bool]:
    """(run, created). Si idempotency_key existe en el mismo proyecto, devuelve (existente, False)."""
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    ikey = (body.idempotency_key or "").strip()
    if not ikey:
        raise HTTPException(400, detail="idempotency_key es obligatoria.")
    ex = await session.execute(select(FieldSyncRun).where(FieldSyncRun.idempotency_key == ikey))
    found = ex.scalars().first()
    if found is not None:
        if found.field_project_id != project_id:
            raise HTTPException(409, detail="idempotency_key ya usada en otro proyecto.")
        return FieldSyncRunPublic.model_validate(found), False

    ex_src = body.field_project_external_source_id
    pol = body.field_policy_set_id

    if ex_src is not None:
        srow = await session.get(FieldProjectExternalSource, ex_src)
        if srow is None or srow.field_project_id != project_id:
            raise NotFoundException("FieldProjectExternalSource no encontrada en este proyecto.")
    if pol is not None:
        prow = await session.get(FieldPolicySet, pol)
        if prow is None or prow.field_project_id != project_id:
            raise NotFoundException("FieldPolicySet no encontrada en este proyecto.")

    run = FieldSyncRun(
        field_project_id=project_id,
        company_id=project.company_id,
        run_kind=RUN_KIND_FIELD_ANALYSIS,
        idempotency_key=ikey,
        field_project_external_source_id=ex_src,
        field_policy_set_id=pol,
        field_import_run_id=None,
        status=SYNC_RUN_PENDING,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return FieldSyncRunPublic.model_validate(run), True


async def set_finding_approval(
    session: AsyncSession,
    user: User,
    project_id: int,
    finding_id: int,
    body: FieldFindingApprovalBody,
) -> FieldFindingPublic:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    f = await session.get(FieldFinding, finding_id)
    if f is None or f.field_project_id != project_id:
        raise NotFoundException("Hallazgo no encontrado en este proyecto.")
    st = (body.status or "").strip().lower()
    if st not in ("approved", "rejected", "pending"):
        raise HTTPException(400, detail="status debe ser approved, rejected o pending.")
    prev = f.approval_status
    note = (body.note or "").strip() or None
    log = FieldFindingDecisionLog(
        company_id=project.company_id,
        field_project_id=project_id,
        field_finding_id=finding_id,
        actor_user_id=user.id,
        from_status=prev,
        to_status=st,
        note=note,
    )
    session.add(log)
    f.approval_status = st
    f.reviewed_by_user_id = user.id
    f.reviewed_at = _utc_now_naive()
    await session.commit()
    await session.refresh(f)
    return FieldFindingPublic.model_validate(f)
