from datetime import datetime
from typing import List
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.payment_model import Payment, PaymentBase, PaymentPublic, PaymentUpdate
from app.utils.exeptions import NotFoundException


async def get_payments(
    session: AsyncSession, offset: int = 0, limit: int = Query(default=10, le=100)
) -> List[PaymentPublic]:
    query = (
        select(Payment)
        .options(selectinload(Payment.company))
        .where(Payment.deleted_at == None)
        .order_by(Payment.id)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    db_payments = result.unique().scalars().all()

    if not db_payments:
        return []

    return [PaymentPublic.model_validate(payment) for payment in db_payments]


async def get_payment(session: AsyncSession, payment_id: int) -> PaymentPublic:
    query = select(Payment).where(Payment.id == payment_id, Payment.deleted_at == None)

    result = await session.execute(query)
    db_payment = result.scalars().first()

    if not db_payment:
        raise NotFoundException("Payment not found")

    return db_payment


async def create_payment(session: AsyncSession, payment: PaymentBase) -> PaymentPublic:
    db_payment = Payment(**payment.model_dump())

    session.add(db_payment)
    await session.commit()
    await session.refresh(db_payment)

    return PaymentPublic.model_validate(db_payment)


async def update_payment(
    session: AsyncSession, payment_id: int, payment: PaymentUpdate
) -> PaymentPublic:
    db_payment = await get_payment(session, payment_id)

    payment_update = payment.model_dump(exclude_unset=True)
    db_payment.sqlmodel_update(payment_update)

    session.add(db_payment)
    await session.commit()
    await session.refresh(db_payment)

    return PaymentPublic.model_validate(db_payment)


async def soft_delete_payment(session: AsyncSession, payment_id: int) -> PaymentPublic:
    db_payment = await get_payment(session, payment_id)

    db_payment.deleted_at = datetime.now()

    session.add(db_payment)
    await session.commit()
    await session.refresh(db_payment)

    return PaymentPublic.model_validate(db_payment)


async def is_company_payment_valid(company_id: int, session: AsyncSession) -> bool:
    query = (
        select(Payment)
        .where(Payment.company_id == company_id)
        .where(Payment.valid_before >= datetime.now())
        .where(Payment.deleted_at == None)
        .order_by(Payment.valid_before.desc())
        .limit(1)
    )
    result = await session.execute(query)
    db_payment = result.scalars().first()

    return db_payment is not None
