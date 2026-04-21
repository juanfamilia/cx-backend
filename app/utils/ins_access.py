"""Acceso al producto Siete InS (separado de CX; habilitación por empresa)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.db import get_db
from app.models.company_model import Company
from app.utils.deps import get_auth_user
from app.utils.exeptions import PermissionDeniedException


async def require_ins_product_access(
    request: Request,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_auth_user),
):
    """
    Rol 0: siempre.
    Resto: empresa con `siete_ins_enabled` (activado por superadmin vía company update).
    """
    user = request.state.user
    if user.role == 0:
        return True
    if user.company_id is None:
        raise PermissionDeniedException(
            custom_message="Siete InS: usuario sin empresa asignada"
        )
    company = await session.get(Company, user.company_id)
    if company is None or not company.siete_ins_enabled:
        raise PermissionDeniedException(
            custom_message="Siete InS no está habilitado para su empresa"
        )
    return True
