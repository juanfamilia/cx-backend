from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.audit_log_model import AuditLogsPublic
from app.services.audit_services import get_audit_logs
from app.utils.deps import get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/audit",
    tags=["Audit Trail"],
    dependencies=[Depends(get_auth_user)],
)


@router.get("/", response_model=AuditLogsPublic)
async def list_logs(
    request: Request,
    session: AsyncSession = Depends(get_db),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    offset: int = 0,
    limit: int = Query(default=50, le=200),
) -> AuditLogsPublic:
    """
    Devuelve registros de auditoría.
    - Superadmin: acceso total.
    - Admin/Gerente: solo los registros de su empresa (filtrado por user_id
      de usuarios de la misma compañía).
    - Evaluador: sin acceso.
    """
    user = request.state.user
    if user.role == 3:
        raise PermissionDeniedException(custom_message="access audit logs")
    return await get_audit_logs(session, entity_type, entity_id, user_id, offset, limit)
