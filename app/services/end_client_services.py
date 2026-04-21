from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.end_client_model import EndClient, EndClientCreate, EndClientPublic
from app.models.user_model import User
from app.utils.exeptions import PermissionDeniedException


def _resolve_company_id(user: User, company_id: Optional[int]) -> int:
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="indique company_id (clientes finales)"
            )
        return cid
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="usuario sin empresa")
    return user.company_id


async def assert_company_staff(user: User) -> None:
    if user.role not in (0, 1, 2):
        raise PermissionDeniedException(
            custom_message="gestionar clientes finales (solo admin o gerente)"
        )


async def list_end_clients(
    session: AsyncSession, user: User, company_id: Optional[int]
) -> list[EndClientPublic]:
    await assert_company_staff(user)
    cid = _resolve_company_id(user, company_id)
    stmt = (
        select(EndClient)
        .where(EndClient.company_id == cid, EndClient.deleted_at.is_(None))
        .order_by(EndClient.name)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [EndClientPublic.model_validate(r) for r in rows]


async def create_end_client(
    session: AsyncSession, user: User, body: EndClientCreate
) -> EndClientPublic:
    await assert_company_staff(user)
    cid = _resolve_company_id(user, body.company_id)
    if user.role != 0 and body.company_id is not None and body.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="company_id no permitido")

    row = EndClient(
        company_id=cid,
        name=body.name.strip(),
        external_ref=(body.external_ref or "").strip() or None,
        notes=(body.notes or "").strip() or None,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return EndClientPublic.model_validate(row)
