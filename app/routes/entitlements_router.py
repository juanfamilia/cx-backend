"""
Entitlements por tenant (`company`): productos CX / InS / Field / Clever.

`GET /entitlements/me` — rol 0 puede pasar `company_id` para consultar otro tenant.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import Company
from app.utils.deps import check_company_payment_status, get_auth_user

router = APIRouter(
    prefix="/entitlements",
    tags=["Entitlements"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


class ProductsPayload(BaseModel):
    cx: bool = Field(default=True, description="CX siempre disponible para el tenant activo.")
    ins: bool
    field: bool
    clever: bool


class MeEntitlementsResponse(BaseModel):
    company_id: int | None
    products: ProductsPayload


@router.get("/me", response_model=MeEntitlementsResponse)
async def get_my_entitlements(
    request: Request,
    session: AsyncSession = Depends(get_db),
    company_id: Optional[int] = Query(
        None,
        description="Rol 0: tenant a consultar. Si se omite y el usuario no tiene company_id, todo en false salvo cx.",
    ),
) -> Any:
    user = request.state.user
    company: Company | None = None

    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is not None:
            company = await session.get(Company, cid)
    elif user.company_id is not None:
        company = await session.get(Company, user.company_id)

    if company is None or company.deleted_at is not None:
        return MeEntitlementsResponse(
            company_id=None,
            products=ProductsPayload(ins=False, field=False, clever=False),
        )

    return MeEntitlementsResponse(
        company_id=company.id,
        products=ProductsPayload(
            cx=True,
            ins=bool(company.siete_ins_enabled),
            field=bool(company.siete_field_enabled),
            clever=bool(company.siete_clever_enabled),
        ),
    )
