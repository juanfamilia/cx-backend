"""Persistencia y lectura de `platform_signal_events` (memoria cross-dominio)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_project_model import FieldProject
from app.models.field_study_model import FieldStudy
from app.models.ins_study_model import InsStudy
from app.models.platform_signal_model import PlatformSignalEvent
from app.platform_intelligence.schemas import PlatformSignalCreateBody, PlatformSignalPublic


async def _assert_refs_for_tenant(
    session: AsyncSession,
    company_id: int,
    body: PlatformSignalCreateBody,
) -> None:
    if body.field_study_id is not None:
        row = await session.get(FieldStudy, body.field_study_id)
        if row is None or row.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="field_study_id no existe o no pertenece al tenant.",
            )
    if body.field_project_id is not None:
        row = await session.get(FieldProject, body.field_project_id)
        if row is None or row.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="field_project_id no existe o no pertenece al tenant.",
            )
    if body.ins_study_id is not None:
        row = await session.get(InsStudy, body.ins_study_id)
        if row is None or row.company_id != company_id or row.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ins_study_id no existe o no pertenece al tenant.",
            )


def _to_public(row: PlatformSignalEvent) -> PlatformSignalPublic:
    return PlatformSignalPublic(
        id=int(row.id),
        company_id=row.company_id,
        source_domain=row.source_domain,
        signal_code=row.signal_code,
        severity=row.severity,
        summary=row.summary,
        payload=row.payload_json or {},
        field_study_id=row.field_study_id,
        field_project_id=row.field_project_id,
        ins_study_id=row.ins_study_id,
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at.isoformat(),
    )


async def create_platform_signal(
    session: AsyncSession,
    *,
    company_id: int,
    user_id: int | None,
    body: PlatformSignalCreateBody,
) -> PlatformSignalPublic:
    await _assert_refs_for_tenant(session, company_id, body)
    row = PlatformSignalEvent(
        company_id=company_id,
        source_domain=body.source_domain,
        signal_code=body.signal_code,
        severity=body.severity,
        summary=body.summary,
        payload_json=dict(body.payload) if body.payload else {},
        field_study_id=body.field_study_id,
        field_project_id=body.field_project_id,
        ins_study_id=body.ins_study_id,
        created_by_user_id=user_id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_public(row)


async def list_recent_signals_public(
    session: AsyncSession,
    company_id: int,
    *,
    limit: int = 15,
) -> list[PlatformSignalPublic]:
    stmt = (
        select(PlatformSignalEvent)
        .where(PlatformSignalEvent.company_id == company_id)
        .order_by(PlatformSignalEvent.created_at.desc())
        .limit(min(limit, 50))
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [_to_public(r) for r in rows]
