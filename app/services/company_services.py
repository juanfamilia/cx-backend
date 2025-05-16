from datetime import datetime
from typing import List
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.company_model import Company, CompanyBase, CompanyPublic, CompanyUpdate
from app.utils.exeptions import NotFoundException


async def get_companies(
    session: AsyncSession, offset: int = 0, limit: int = Query(default=10, le=100)
) -> List[CompanyPublic]:

    query = (
        select(Company)
        .where(Company.deleted_at == None)
        .order_by(Company.id)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    db_companies = result.scalars().all()

    if not db_companies:
        return []

    return [CompanyPublic.model_validate(company) for company in db_companies]


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
