from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.end_client_model import EndClient
from app.models.field_project_model import (
    FieldProject,
    FieldProjectCreate,
    FieldProjectPublic,
)
from app.models.user_model import User
from app.utils.exeptions import PermissionDeniedException


def _company_id_for_write(user: User, body_company_id: Optional[int]) -> int:
    if user.role == 0:
        cid = body_company_id if body_company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="crear proyecto Field: indique company_id"
            )
        return cid
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="sin empresa")
    return user.company_id


async def assert_field_staff(user: User) -> None:
    if user.role not in (0, 1, 2):
        raise PermissionDeniedException(
            custom_message="gestionar Field (solo admin o gerente)"
        )


async def _assert_client_belongs_to_company(
    session: AsyncSession, client_id: int, company_id: int
) -> None:
    ec = await session.get(EndClient, client_id)
    if ec is None or ec.deleted_at is not None or ec.company_id != company_id:
        raise PermissionDeniedException(custom_message="cliente final inválido")


async def list_field_projects(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    client_id: Optional[int],
) -> list[FieldProjectPublic]:
    await assert_field_staff(user)
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="listar proyectos Field: indique company_id"
            )
    else:
        cid = user.company_id
        if cid is None:
            return []

    stmt = select(FieldProject).where(
        FieldProject.company_id == cid,
        FieldProject.deleted_at.is_(None),
    )
    if client_id is not None:
        stmt = stmt.where(FieldProject.client_id == client_id)
    stmt = stmt.order_by(FieldProject.updated_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldProjectPublic.model_validate(r) for r in rows]


async def create_field_project(
    session: AsyncSession, user: User, body: FieldProjectCreate
) -> FieldProjectPublic:
    await assert_field_staff(user)
    cid = _company_id_for_write(user, body.company_id)
    if user.role != 0 and body.company_id not in (None, user.company_id):
        raise PermissionDeniedException(custom_message="company_id no permitido")

    await _assert_client_belongs_to_company(session, body.client_id, cid)

    row = FieldProject(
        company_id=cid,
        client_id=body.client_id,
        name=body.name.strip(),
        description=(body.description or "").strip() or None,
        import_format_version="2026.1",
        status="draft",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FieldProjectPublic.model_validate(row)
