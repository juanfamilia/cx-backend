from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import (
    CompaniesPublic,
    CompanyBase,
    CompanyPublic,
    CompanyUpdate,
)
from app.services.company_services import (
    create_company,
    get_companies,
    get_company,
    soft_delete_company,
    update_company,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/company",
    tags=["Company"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> CompaniesPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="retrieve companies")

    companies = await get_companies(session, offset, limit, filter, search)

    return companies


@router.get("/{company_id}")
async def get_one(
    request: Request,
    company_id: int,
    session: AsyncSession = Depends(get_db),
) -> CompanyPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="retrieve this company")

    company = await get_company(session, company_id)

    return company


@router.post("/")
async def create(
    request: Request,
    company_create: CompanyBase,
    session: AsyncSession = Depends(get_db),
) -> CompanyPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="create a company")

    company = await create_company(session, company_create)

    return company


@router.put("/{company_id}")
async def update(
    request: Request,
    company_id: int,
    company_update: CompanyUpdate,
    session: AsyncSession = Depends(get_db),
) -> CompanyPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="update this company")

    company = await update_company(session, company_id, company_update)

    return company


@router.delete("/{company_id}")
async def delete(
    request: Request,
    company_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="delete this company")

    await soft_delete_company(session, company_id)

    return {"message": "Company deleted"}
