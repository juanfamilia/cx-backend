from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.end_client_model import EndClient
from app.models.field_study_model import FieldStudy, FieldStudyCreate, FieldStudyPublic
from app.models.user_model import User
from app.platform_intelligence.signals_service import emit_platform_signal_safe
from app.services.field_project_services import (
    _company_id_for_write,
    assert_field_staff,
)
from app.services.field_study_brief_services import ensure_field_study_brief_row
from app.utils.exeptions import PermissionDeniedException


async def _assert_client_belongs_to_company(
    session: AsyncSession, client_id: int, company_id: int
) -> None:
    ec = await session.get(EndClient, client_id)
    if ec is None or ec.deleted_at is not None or ec.company_id != company_id:
        raise PermissionDeniedException(custom_message="cliente final inválido")


async def list_field_studies(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    client_id: Optional[int],
) -> list[FieldStudyPublic]:
    await assert_field_staff(user)
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="listar estudios Field: indique company_id"
            )
    else:
        cid = user.company_id
        if cid is None:
            return []

    stmt = select(FieldStudy).where(FieldStudy.company_id == cid)
    if client_id is not None:
        stmt = stmt.where(FieldStudy.client_id == client_id)
    stmt = stmt.order_by(FieldStudy.updated_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldStudyPublic.model_validate(r) for r in rows]


async def create_field_study(
    session: AsyncSession, user: User, body: FieldStudyCreate
) -> FieldStudyPublic:
    await assert_field_staff(user)
    cid = _company_id_for_write(user, body.company_id)
    if user.role != 0 and body.company_id not in (None, user.company_id):
        raise PermissionDeniedException(custom_message="company_id no permitido")

    await _assert_client_belongs_to_company(session, body.client_id, cid)

    row = FieldStudy(
        company_id=cid,
        client_id=body.client_id,
        name=body.name.strip(),
        description=(body.description or "").strip() or None,
        status="draft",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    await ensure_field_study_brief_row(session, row.id, cid)
    await emit_platform_signal_safe(
        session,
        company_id=cid,
        user_id=user.id,
        source_domain="field",
        signal_code="field.study_created",
        summary=f"Field: estudio canónico «{row.name[:280]}»",
        severity="low",
        payload={
            "field_study_id": row.id,
            "client_id": row.client_id,
            "status": row.status,
        },
        field_study_id=row.id,
    )
    return FieldStudyPublic.model_validate(row)
