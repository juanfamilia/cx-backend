"""Lectura de la capa de decisión Field (fuentes externas, políticas, snapshot)."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_decision_model import (
    FieldOperationalSnapshot,
    FieldOperationalSnapshotPublic,
    FieldPolicySet,
    FieldPolicySetPublic,
    FieldProjectExternalSource,
    FieldProjectExternalSourcePublic,
)
from app.models.field_project_model import FieldProject
from app.models.user_model import User
from app.services.field_project_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException


def _assert_project_access(user: User, project: FieldProject) -> None:
    if user.role == 0:
        return
    if user.company_id is None or project.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="proyecto Field no permitido")


async def _get_project(session: AsyncSession, project_id: int) -> FieldProject:
    row = await session.get(FieldProject, project_id)
    if row is None or row.deleted_at is not None:
        raise NotFoundException("Proyecto Field no encontrado")
    return row


async def list_external_sources(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldProjectExternalSourcePublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    stmt = (
        select(FieldProjectExternalSource)
        .where(FieldProjectExternalSource.field_project_id == project_id)
        .order_by(FieldProjectExternalSource.id)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldProjectExternalSourcePublic.model_validate(r) for r in rows]


async def list_policy_sets(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldPolicySetPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    stmt = (
        select(FieldPolicySet)
        .where(FieldPolicySet.field_project_id == project_id)
        .order_by(FieldPolicySet.version.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldPolicySetPublic.model_validate(r) for r in rows]


async def get_operational_snapshot(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> FieldOperationalSnapshotPublic | None:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    stmt = select(FieldOperationalSnapshot).where(
        FieldOperationalSnapshot.field_project_id == project_id
    )
    row = (await session.execute(stmt)).scalars().first()
    if row is None:
        return None
    return FieldOperationalSnapshotPublic.model_validate(row)
