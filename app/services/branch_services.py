from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.branch_model import (
    Branch,
    BranchCreate,
    BranchImportResult,
    BranchImportRow,
    BranchUpdate,
    BranchesPublic,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_branches(
    session: AsyncSession,
    company_id: int,
    offset: int = 0,
    limit: int = 50,
    zone_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> BranchesPublic:
    conditions = [
        Branch.company_id == company_id,
        Branch.deleted_at.is_(None),
    ]
    if zone_id is not None:
        conditions.append(Branch.zone_id == zone_id)
    if is_active is not None:
        conditions.append(Branch.is_active == is_active)
    if search:
        conditions.append(
            Branch.name.ilike(f"%{search}%") | Branch.code.ilike(f"%{search}%")
        )

    count_q = select(func.count(Branch.id)).where(*conditions)
    total = (await session.execute(count_q)).scalar_one()

    q = (
        select(Branch)
        .where(*conditions)
        .order_by(Branch.name)
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(q)).scalars().all()

    return BranchesPublic(
        data=list(rows),
        pagination=Pagination(total=total, offset=offset, limit=limit),
    )


async def get_branch(session: AsyncSession, branch_id: int) -> Branch:
    branch = await session.get(Branch, branch_id)
    if not branch or branch.deleted_at is not None:
        raise NotFoundException("Branch not found")
    return branch


async def get_branch_by_code(
    session: AsyncSession, company_id: int, code: str
) -> Optional[Branch]:
    q = select(Branch).where(
        Branch.company_id == company_id,
        Branch.code == code,
        Branch.deleted_at.is_(None),
    )
    return (await session.execute(q)).scalars().first()


async def create_branch(session: AsyncSession, payload: BranchCreate) -> Branch:
    branch = Branch(**payload.model_dump())
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


async def update_branch(
    session: AsyncSession, branch_id: int, payload: BranchUpdate
) -> Branch:
    branch = await get_branch(session, branch_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(branch, key, value)
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


async def delete_branch(session: AsyncSession, branch_id: int) -> Branch:
    from datetime import datetime, timezone

    branch = await get_branch(session, branch_id)
    branch.deleted_at = datetime.now(timezone.utc)
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


async def bulk_import_branches(
    session: AsyncSession,
    company_id: int,
    rows: List[BranchImportRow],
) -> BranchImportResult:
    """
    Upsert masivo: crea si no existe el código, actualiza si ya existe.
    Retorna resumen con conteos y lista de errores por fila.
    """
    created = 0
    updated = 0
    errors: List[str] = []

    for row in rows:
        try:
            existing = await get_branch_by_code(session, company_id, row.code)
            if existing:
                existing.name = row.name
                if row.zone_id is not None:
                    existing.zone_id = row.zone_id
                if row.address is not None:
                    existing.address = row.address
                existing.country = row.country
                session.add(existing)
                updated += 1
            else:
                branch = Branch(
                    company_id=company_id,
                    code=row.code,
                    name=row.name,
                    zone_id=row.zone_id,
                    address=row.address,
                    country=row.country,
                )
                session.add(branch)
                created += 1
        except Exception as exc:
            errors.append(f"code={row.code}: {exc}")

    await session.commit()
    return BranchImportResult(created=created, updated=updated, errors=errors)
