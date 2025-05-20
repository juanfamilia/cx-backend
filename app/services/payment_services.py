from datetime import date, datetime
from typing import List, Optional
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import String, func, select
from sqlalchemy.orm import selectinload

from app.models.company_model import Company
from app.models.payment_model import (
    Payment,
    PaymentBase,
    PaymentPublic,
    PaymentUpdate,
    PaymentsPublic,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_payments(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> PaymentsPublic:

    query = (
        select(Payment, func.count().over().label("total"))
        .join(Company, Payment.company_id == Company.id, isouter=True)  # LEFT JOIN
        .options(selectinload(Payment.company))
        .where(Payment.deleted_at.is_(None))
    )

    if filter and search:
        match filter:
            case "company":
                query = query.where(Company.name.ilike(f"%{search}%"))

            case "amount":
                try:
                    search_value = int(search)
                    query = query.where(Payment.amount == search_value)
                except ValueError:
                    raise NotFoundException("Invalid amount")

            case "date":
                try:
                    search_date = date.fromisoformat(search)
                    query = query.where(func.date(Payment.date) == search_date)
                except ValueError:
                    query = query.where(
                        func.cast(Payment.date, String).ilike(f"%{search}%")
                    )

            case "valid_before":
                try:
                    search_date = date.fromisoformat(search)
                    query = query.where(Payment.valid_before == search_date)
                except ValueError:
                    query = query.where(
                        func.cast(Payment.valid_before, String).ilike(f"%{search}%")
                    )

    query = query.order_by(Payment.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_payments = result.unique().all()

    if not db_payments:
        raise NotFoundException("Payments not found")

    payments = [row[0] for row in db_payments]
    total = db_payments[0][1] if db_payments else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return PaymentsPublic(data=payments, pagination=pagination)


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
