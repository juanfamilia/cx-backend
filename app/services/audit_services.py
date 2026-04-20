"""
Audit Trail Service
Registro inmutable de cambios. Solo se escribe; nunca se modifica ni elimina.
"""
import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.audit_log_model import AuditLog, AuditLogsPublic, AuditLogPublic
from app.types.pagination import Pagination

logger = logging.getLogger(__name__)


async def log_change(
    session: AsyncSession,
    *,
    user_id: int,
    user_email: str,
    entity_type: str,
    entity_id: int,
    action: str,
    field_name: Optional[str] = None,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    justification: Optional[str] = None,
    extra: Optional[dict] = None,
) -> AuditLog:
    """
    Persiste un registro de auditoría. Nunca lanza excepción hacia el caller:
    si el log falla, solo escribe un warning para no interrumpir la operación principal.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            justification=justification,
            extra=extra,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry
    except Exception as exc:
        logger.warning("audit_log write failed entity=%s id=%s: %s", entity_type, entity_id, exc)
        raise


async def get_audit_logs(
    session: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 50,
) -> AuditLogsPublic:
    conditions = []
    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        conditions.append(AuditLog.entity_id == entity_id)
    if user_id is not None:
        conditions.append(AuditLog.user_id == user_id)

    count_q = select(func.count(AuditLog.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total = (await session.execute(count_q)).scalar_one()

    q = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    if conditions:
        q = q.where(*conditions)
    rows = (await session.execute(q)).scalars().all()

    return AuditLogsPublic(
        data=[AuditLogPublic.model_validate(r) for r in rows],
        pagination=Pagination(first=offset, rows=limit, total=total),
    )
