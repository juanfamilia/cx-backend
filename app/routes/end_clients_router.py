"""Clientes finales (sub-tenant) por empresa."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.end_client_model import EndClientCreate, EndClientPublic
from app.services.end_client_services import create_end_client, list_end_clients
from app.utils.deps import check_company_payment_status, get_auth_user

router = APIRouter(
    prefix="/end-clients",
    tags=["End clients"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("", response_model=list[EndClientPublic])
async def list_clients(
    request: Request,
    company_id: Optional[int] = Query(
        None,
        description="Rol 0: obligatorio salvo que el usuario tenga company_id asignada.",
    ),
    session: AsyncSession = Depends(get_db),
):
    return await list_end_clients(session, request.state.user, company_id)


@router.post("", response_model=EndClientPublic)
async def create_client(
    request: Request,
    body: EndClientCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_end_client(session, request.state.user, body)
