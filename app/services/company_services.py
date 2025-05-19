from datetime import datetime
from typing import List, Optional
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.company_model import (
    CompaniesPublic,
    Company,
    CompanyBase,
    CompanyPublic,
    CompanyUpdate,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_companies(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> CompaniesPublic:

    query = select(Company, func.count().over().label("total")).where(
        Company.deleted_at == None
    )

    if filter and search:
        match filter:
            case "name":
                query = query.where(Company.name.ilike(f"%{search}%"))

            case "phone":
                query = query.where(Company.phone.ilike(f"%{search}%"))

            case "email":
                query = query.where(Company.email.ilike(f"%{search}%"))

    query = query.order_by(Company.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_companies = result.unique().all()

    if not db_companies:
        raise NotFoundException("Companies not found")

    companies = [row[0] for row in db_companies]
    total = db_companies[0][1] if db_companies else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return CompaniesPublic(data=companies, pagination=pagination)


async def get_company(session: AsyncSession, company_id: int) -> CompanyPublic:
    query = select(Company).where(Company.id == company_id, Company.deleted_at == None)

    result = await session.execute(query)
    db_company = result.scalars().first()

    if not db_company:
        raise NotFoundException("Company not found")

    return db_company


async def create_company(session: AsyncSession, company: CompanyBase) -> CompanyPublic:
    db_company = Company(**company.model_dump())

    session.add(db_company)
    await session.commit()
    await session.refresh(db_company)

    return CompanyPublic.model_validate(db_company)


async def update_company(
    session: AsyncSession, company_id: int, company: CompanyUpdate
) -> CompanyPublic:
    db_company = await get_company(session, company_id)

    company_update = company.model_dump(exclude_unset=True)
    db_company.sqlmodel_update(company_update)

    session.add(db_company)
    await session.commit()
    await session.refresh(db_company)

    return CompanyPublic.model_validate(db_company)


async def soft_delete_company(session: AsyncSession, company_id: int) -> CompanyPublic:
    db_company = await get_company(session, company_id)

    db_company.deleted_at = datetime.now()

    session.add(db_company)
    await session.commit()
    await session.refresh(db_company)

    return CompanyPublic.model_validate(db_company)
