"""PRE-FIELD — CRUD de revisiones `instrument_spec` y validación schema persistente."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.field_instrument_revision_model import (
    FieldInstrumentRevision,
    FieldInstrumentRevisionCreate,
    FieldInstrumentRevisionPatch,
    FieldInstrumentRevisionPublic,
    FieldInstrumentRevisionValidateResponse,
    InstrumentSpecSchemaIssue,
    InstrumentSpecValidationReport,
)
from app.models.field_study_model import FieldStudy
from app.models.user_model import User
from app.services.field_framework_template_services import get_field_framework_template_by_slug_version
from app.services.field_study_services import assert_field_staff
from app.services.instrument_spec_validate import (
    compute_instrument_spec_content_hash,
    validate_instrument_spec,
)
from app.utils.exeptions import NotFoundException, PermissionDeniedException


DEFAULT_INSTRUMENT_SPEC_STUB: dict[str, Any] = {
    "instrument_spec_version": "2026.1-draft",
    "title": "Borrador",
    "blocks": [
        {
            "block_id": "B01",
            "title": "Sección inicial",
            "items": [],
        },
    ],
}


def _effective_company_id(user: User, company_id: Optional[int]) -> int:
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="operaciones Field PRE-FIELD: indique company_id"
            )
        return cid
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="sin empresa")
    return user.company_id


def _assert_spec_object(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="instrument_spec debe ser un objeto JSON en la raíz",
        )
    return spec


def _derive_spec_metadata(spec: dict[str, Any]) -> tuple[str | None, str | None]:
    title_v = spec.get("title")
    title = title_v.strip() if isinstance(title_v, str) else None
    ver_v = spec.get("instrument_spec_version")
    ver = ver_v.strip() if isinstance(ver_v, str) else None
    return title, ver


def build_instrument_spec_validation_report(spec: dict[str, Any]) -> InstrumentSpecValidationReport:
    messages = validate_instrument_spec(spec)
    fixed_issues: list[InstrumentSpecSchemaIssue] = []
    for m in messages:
        if ": " in m:
            p, msg = m.split(": ", 1)
            fixed_issues.append(InstrumentSpecSchemaIssue(path=p, message=msg))
        else:
            fixed_issues.append(InstrumentSpecSchemaIssue(path="(root)", message=m))
    ver_v = spec.get("instrument_spec_version")
    ver = ver_v.strip() if isinstance(ver_v, str) else None
    chash = compute_instrument_spec_content_hash(spec)
    return InstrumentSpecValidationReport(
        ok=len(messages) == 0,
        instrument_spec_version=ver,
        content_hash=chash,
        schema_issues=fixed_issues,
    )


async def _get_study_for_company(
    session: AsyncSession,
    study_id: int,
    company_id: int,
) -> FieldStudy:
    st = await session.get(FieldStudy, study_id)
    if st is None:
        raise NotFoundException("Estudio Field no encontrado")
    if st.company_id != company_id:
        raise PermissionDeniedException(custom_message="estudio Field no permitido")
    return st


async def _get_revision_writable(
    session: AsyncSession,
    revision_id: int,
    company_id: int,
) -> FieldInstrumentRevision:
    row = await session.get(FieldInstrumentRevision, revision_id)
    if row is None or row.deleted_at is not None:
        raise NotFoundException("Revisión de instrumento no encontrada")
    if row.company_id != company_id:
        raise PermissionDeniedException(custom_message="revisión no permitida")
    return row


async def _allocate_revision_label(session: AsyncSession, study_id: int) -> str:
    stmt = select(func.count()).select_from(FieldInstrumentRevision).where(
        FieldInstrumentRevision.study_id == study_id,
        FieldInstrumentRevision.deleted_at.is_(None),
    )
    n = int((await session.execute(stmt)).scalar_one() or 0) + 1
    return f"v{n}"


async def list_instrument_revisions_for_study(
    session: AsyncSession,
    user: User,
    study_id: int,
    company_id: Optional[int],
) -> list[FieldInstrumentRevisionPublic]:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    await _get_study_for_company(session, study_id, cid)

    stmt = (
        select(FieldInstrumentRevision)
        .where(
            FieldInstrumentRevision.study_id == study_id,
            FieldInstrumentRevision.company_id == cid,
            FieldInstrumentRevision.deleted_at.is_(None),
        )
        .order_by(FieldInstrumentRevision.updated_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldInstrumentRevisionPublic.model_validate(r) for r in rows]


async def create_instrument_revision(
    session: AsyncSession,
    user: User,
    study_id: int,
    body: FieldInstrumentRevisionCreate,
    company_id: Optional[int],
) -> FieldInstrumentRevisionPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    await _get_study_for_company(session, study_id, cid)

    slug = body.framework_template_slug
    need_stub_from_template = body.spec is None
    tpl_row = None
    tpl_ref: str | None = None
    if slug:
        ver = (body.framework_template_version or "2026.1").strip()
        tpl_row = await get_field_framework_template_by_slug_version(session, slug, ver)
        if tpl_row is None:
            if need_stub_from_template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plantilla framework no encontrada o inactiva",
                )
            tpl_row = None
        else:
            tpl_ref = f"{tpl_row.slug}@{tpl_row.framework_version}"

    if body.spec is not None:
        spec = _assert_spec_object(body.spec)
    elif tpl_row is not None:
        if tpl_row.stub_spec_json is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Plantilla sin stub_spec_json",
            )
        spec = _assert_spec_object(dict(tpl_row.stub_spec_json))
    else:
        spec = _assert_spec_object(DEFAULT_INSTRUMENT_SPEC_STUB)
    title, ver_decl = _derive_spec_metadata(spec)
    content_hash = compute_instrument_spec_content_hash(spec)

    label = body.revision_label
    if label is None:
        label = await _allocate_revision_label(session, study_id)

    row = FieldInstrumentRevision(
        study_id=study_id,
        company_id=cid,
        revision_label=label,
        status="draft",
        framework_template_id=tpl_ref
        if tpl_ref is not None
        else ((body.framework_template_id or "").strip() or None),
        notes=(body.notes or "").strip() or None,
        title=title,
        instrument_spec_version_declared=ver_decl,
        spec_json=spec,
        content_hash=content_hash,
        created_by_user_id=user.id,
        updated_by_user_id=user.id,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="revision_label ya existe para este estudio (activo)",
        ) from None
    await session.refresh(row)
    return FieldInstrumentRevisionPublic.model_validate(row)


async def get_instrument_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
    *,
    include_spec: bool = False,
) -> tuple[FieldInstrumentRevisionPublic, dict[str, Any] | None]:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _get_revision_writable(session, revision_id, cid)
    pub = FieldInstrumentRevisionPublic.model_validate(row)
    spec = dict(row.spec_json) if include_spec else None
    return pub, spec


async def patch_instrument_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    body: FieldInstrumentRevisionPatch,
    company_id: Optional[int],
) -> FieldInstrumentRevisionPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _get_revision_writable(session, revision_id, cid)

    if row.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="solo revisiones en estado draft son editables",
        )

    if body.spec is not None:
        spec = _assert_spec_object(body.spec)
        row.spec_json = spec
        title, ver_decl = _derive_spec_metadata(spec)
        row.title = title
        row.instrument_spec_version_declared = ver_decl
        row.content_hash = compute_instrument_spec_content_hash(spec)

    if body.framework_template_id is not None:
        row.framework_template_id = body.framework_template_id.strip() or None
    if body.notes is not None:
        row.notes = body.notes.strip() or None

    if body.revision_label is not None:
        row.revision_label = body.revision_label

    if body.status is not None:
        if body.status != "archived":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="status solo admite archived en esta versión de API",
            )
        row.status = "archived"

    row.updated_by_user_id = user.id

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="revision_label ya existe para este estudio (activo)",
        ) from None
    await session.refresh(row)
    return FieldInstrumentRevisionPublic.model_validate(row)


async def validate_instrument_spec_inline(
    user: User,
    spec: dict[str, Any],
) -> InstrumentSpecValidationReport:
    """Validación stateless (sin persistencia)."""
    await assert_field_staff(user)
    spec = _assert_spec_object(spec)
    return build_instrument_spec_validation_report(spec)


async def validate_instrument_revision_and_persist(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
) -> FieldInstrumentRevisionValidateResponse:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _get_revision_writable(session, revision_id, cid)

    if row.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="solo revisiones en borrador admiten validación schema persistente",
        )

    spec = _assert_spec_object(dict(row.spec_json))
    report = build_instrument_spec_validation_report(spec)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row.last_validation_at = now
    row.last_validation_ok = report.ok
    row.last_validation_issue_count = len(report.schema_issues)
    row.last_validation_content_hash = report.content_hash
    row.updated_by_user_id = user.id

    await session.commit()
    await session.refresh(row)

    return FieldInstrumentRevisionValidateResponse(
        revision=FieldInstrumentRevisionPublic.model_validate(row),
        report=report,
    )
