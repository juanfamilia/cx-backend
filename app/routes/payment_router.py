from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.payment_model import (
    PaymentBase,
    PaymentPublic,
    PaymentUpdate,
    PaymentsPublic,
)
from app.services.payment_services import (
    create_payment,
    get_payment,
    get_payments,
    soft_delete_payment,
    update_payment,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/payment",
    tags=["Payment"],
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
) -> PaymentsPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="retrieve payments")

    payments = await get_payments(session, offset, limit, filter, search)

    return payments


@router.get("/{payment_id}")
async def get_one(
    request: Request,
    payment_id: int,
    session: AsyncSession = Depends(get_db),
) -> PaymentPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="retrieve this payment")

    payment = await get_payment(session, payment_id)

    return payment


@router.post("/")
async def create(
    request: Request,
    payment: PaymentBase,
    session: AsyncSession = Depends(get_db),
) -> PaymentPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="create a payment")

    if payment.date is not None:
        payment.date = payment.date.replace(tzinfo=None)

    if payment.valid_before is not None:
        payment.valid_before = payment.valid_before.replace(tzinfo=None)

    payment = await create_payment(session, payment)

    return payment


@router.put("/{payment_id}")
async def update(
    request: Request,
    payment_id: int,
    payment_update: PaymentUpdate,
    session: AsyncSession = Depends(get_db),
) -> PaymentPublic:

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="update this payment")

    if payment_update.date is not None:
        payment_update.date = payment_update.date.replace(tzinfo=None)

    if payment_update.valid_before is not None:
        payment_update.valid_before = payment_update.valid_before.replace(tzinfo=None)

    payment = await update_payment(session, payment_id, payment_update)

    return payment


@router.delete("/{payment_id}")
async def delete(
    request: Request,
    payment_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role != 0:
        raise PermissionDeniedException(custom_message="delete this payment")

    await soft_delete_payment(session, payment_id)

    return {"message": "Payment deleted"}
