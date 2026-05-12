"""Framework waiver PRE-FIELD — auditado por revisión de instrumento."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_framework_waiver_model import (
    FieldFrameworkWaiver,
    FieldFrameworkWaiverCreate,
    FieldFrameworkWaiverPublic,
)
from app.models.user_model import User
from app.services.field_instrument_revision_services import (
    _effective_company_id,
    _get_revision_writable,
)
from app.services.field_study_services import assert_field_staff


async def create_framework_waiver_for_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    body: FieldFrameworkWaiverCreate,
    company_id: Optional[int],
) -> FieldFrameworkWaiverPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    rev = await _get_revision_writable(session, revision_id, cid)

    if rev.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="solo revisiones draft admiten registrar waiver explícito",
        )

    rationale = body.rationale.strip()
    if len(rationale) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rationale demasiado corto para auditoría",
        )

    row = FieldFrameworkWaiver(
        instrument_revision_id=revision_id,
        company_id=cid,
        rationale=rationale,
        waived_sections_json=body.waived_sections,
        created_by_user_id=user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FieldFrameworkWaiverPublic.model_validate(row)


async def list_framework_waivers_for_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
) -> list[FieldFrameworkWaiverPublic]:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    await _get_revision_writable(session, revision_id, cid)

    stmt = (
        select(FieldFrameworkWaiver)
        .where(
            FieldFrameworkWaiver.instrument_revision_id == revision_id,
            FieldFrameworkWaiver.company_id == cid,
        )
        .order_by(FieldFrameworkWaiver.created_at.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldFrameworkWaiverPublic.model_validate(r) for r in rows]
