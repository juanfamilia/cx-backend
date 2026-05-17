"""Brief PRE-FIELD por estudio — hash estable para snapshots en revisiones."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_study_brief_model import (
    FieldStudyBrief,
    FieldStudyBriefPatch,
    FieldStudyBriefPublic,
)
from app.models.field_study_model import FieldStudy
from app.models.user_model import User
from app.platform_intelligence.signals_service import emit_platform_signal_safe
from app.services.field_project_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException

BRIEF_APPROVED_FOR_READINESS = frozenset({"approved_internal", "approved"})


def _effective_company_id(user: User, company_id: Optional[int]) -> int:
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="operaciones Field brief: indique company_id"
            )
        return cid
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="sin empresa")
    return user.company_id


def compute_brief_body_hash(payload: dict[str, Any]) -> str:
    """Serialización canónica para lineage (sorted keys, utf-8)."""
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def _get_study_for_company(
    session: AsyncSession,
    study_id: int,
    company_id: int,
) -> FieldStudy:
    stmt = select(FieldStudy).where(FieldStudy.id == study_id)
    st = (await session.execute(stmt)).scalar_one_or_none()
    if st is None:
        raise NotFoundException("Estudio Field no encontrado")
    if st.company_id != company_id:
        raise PermissionDeniedException(custom_message="estudio Field no permitido")
    return st


async def _select_brief_for_study_company(
    session: AsyncSession,
    study_id: int,
    company_id: int,
) -> FieldStudyBrief | None:
    stmt = select(FieldStudyBrief).where(
        FieldStudyBrief.study_id == study_id,
        FieldStudyBrief.company_id == company_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def ensure_field_study_brief_row(
    session: AsyncSession,
    study_id: int,
    company_id: int,
) -> FieldStudyBrief:
    stmt = select(FieldStudyBrief).where(FieldStudyBrief.study_id == study_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is not None:
        return row
    await _get_study_for_company(session, study_id, company_id)
    row = FieldStudyBrief(
        study_id=study_id,
        company_id=company_id,
        payload_json={},
        body_hash=compute_brief_body_hash({}),
        approval_state="draft",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_field_study_brief_public(
    session: AsyncSession,
    user: User,
    study_id: int,
    company_id: Optional[int],
) -> FieldStudyBriefPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    existing = await _select_brief_for_study_company(session, study_id, cid)
    if existing is not None:
        return FieldStudyBriefPublic.model_validate(existing)
    await _get_study_for_company(session, study_id, cid)
    row = await ensure_field_study_brief_row(session, study_id, cid)
    return FieldStudyBriefPublic.model_validate(row)


async def patch_field_study_brief(
    session: AsyncSession,
    user: User,
    study_id: int,
    body: FieldStudyBriefPatch,
    company_id: Optional[int],
) -> FieldStudyBriefPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _select_brief_for_study_company(session, study_id, cid)
    if row is None:
        await _get_study_for_company(session, study_id, cid)
        row = await ensure_field_study_brief_row(session, study_id, cid)

    if row.approval_state in BRIEF_APPROVED_FOR_READINESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="brief ya aprobado: crear nueva versión de brief en backlog o revertir estado explícitamente",
        )

    if body.payload is not None:
        row.payload_json = body.payload
        row.body_hash = compute_brief_body_hash(dict(body.payload))
    if body.completeness_score is not None:
        row.completeness_score = body.completeness_score

    row.updated_by_user_id = user.id
    await session.commit()
    await session.refresh(row)
    return FieldStudyBriefPublic.model_validate(row)


async def approve_field_study_brief_internal(
    session: AsyncSession,
    user: User,
    study_id: int,
    company_id: Optional[int],
) -> FieldStudyBriefPublic:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _select_brief_for_study_company(session, study_id, cid)
    if row is None:
        await _get_study_for_company(session, study_id, cid)
        row = await ensure_field_study_brief_row(session, study_id, cid)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row.approval_state = "approved_internal"
    row.approved_internal_user_id = user.id
    row.approved_internal_at = now
    row.updated_by_user_id = user.id
    await session.commit()
    await session.refresh(row)
    st = await session.get(FieldStudy, study_id)
    study_label = (st.name[:240] if st and st.name else f"estudio {study_id}")
    await emit_platform_signal_safe(
        session,
        company_id=cid,
        user_id=user.id,
        source_domain="pre_field",
        signal_code="pre_field.brief_approved_internal",
        summary=f"PRE-FIELD: brief aprobado internamente — «{study_label}»",
        severity="low",
        payload={
            "field_study_id": study_id,
            "approval_state": row.approval_state,
            "brief_body_hash": row.body_hash,
        },
        field_study_id=study_id,
    )
    return FieldStudyBriefPublic.model_validate(row)


async def approve_field_study_brief_client(
    session: AsyncSession,
    user: User,
    study_id: int,
    company_id: Optional[int],
) -> FieldStudyBriefPublic:
    """Marca visto bueno cliente (modelo B2B2B); staff autorizado."""
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    row = await _select_brief_for_study_company(session, study_id, cid)
    if row is None:
        await _get_study_for_company(session, study_id, cid)
        row = await ensure_field_study_brief_row(session, study_id, cid)

    if row.approval_state == "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="requiere approved_internal antes de approved cliente",
        )

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row.approval_state = "approved"
    row.approved_client_user_id = user.id
    row.approved_client_at = now
    row.updated_by_user_id = user.id
    await session.commit()
    await session.refresh(row)
    st = await session.get(FieldStudy, study_id)
    study_label = (st.name[:240] if st and st.name else f"estudio {study_id}")
    await emit_platform_signal_safe(
        session,
        company_id=cid,
        user_id=user.id,
        source_domain="pre_field",
        signal_code="pre_field.brief_approved_client",
        summary=f"PRE-FIELD: brief aprobado por cliente — «{study_label}»",
        severity="low",
        payload={
            "field_study_id": study_id,
            "approval_state": row.approval_state,
            "brief_body_hash": row.body_hash,
        },
        field_study_id=study_id,
    )
    return FieldStudyBriefPublic.model_validate(row)


def brief_allows_readiness(row: FieldStudyBrief | None) -> bool:
    if row is None:
        return False
    return row.approval_state in BRIEF_APPROVED_FOR_READINESS
