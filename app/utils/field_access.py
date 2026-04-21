"""Acceso al producto Siete Field (habilitación por empresa)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.db import get_db
from app.models.company_model import Company
from app.utils.deps import get_auth_user
from app.utils.exeptions import PermissionDeniedException


async def require_field_product_access(
    request: Request,
    session: AsyncSession = Depends(get_db),
    _user=Depends(get_auth_user),
):
    user = request.state.user
    if user.role == 0:
        return True
    if user.company_id is None:
        raise PermissionDeniedException(
            custom_message="Siete Field: usuario sin empresa asignada"
        )
    company = await session.get(Company, user.company_id)
    if company is None or not company.siete_field_enabled:
        raise PermissionDeniedException(
            custom_message="Siete Field no está habilitado para su empresa"
        )
    return True
