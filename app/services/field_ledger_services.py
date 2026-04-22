"""Lectura del Execution Ledger Field (corridas, filas, hallazgos, eventos)."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_ledger_model import (
    FieldFinding,
    FieldFindingPublic,
    FieldImportRow,
    FieldImportRowPublic,
    FieldLedgerEvent,
    FieldLedgerEventPublic,
)
from app.models.field_project_model import FieldImportRun, FieldImportRunPublic, FieldProject
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


async def _get_run_in_project(
    session: AsyncSession, project_id: int, run_id: int
) -> FieldImportRun:
    r = await session.get(FieldImportRun, run_id)
    if r is None or r.field_project_id != project_id:
        raise NotFoundException("Corrida de import no encontrada")
    return r


async def list_import_runs_for_project(
    session: AsyncSession,
    user: User,
    project_id: int,
    limit: int = 50,
) -> list[FieldImportRunPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)

    stmt = (
        select(FieldImportRun)
        .where(FieldImportRun.field_project_id == project_id)
        .order_by(FieldImportRun.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [FieldImportRunPublic.model_validate(r) for r in rows]


async def list_rows_for_run(
    session: AsyncSession,
    user: User,
    project_id: int,
    run_id: int,
    offset: int = 0,
    limit: int = 100,
) -> list[FieldImportRowPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    await _get_run_in_project(session, project_id, run_id)

    stmt = (
        select(FieldImportRow)
        .where(
            FieldImportRow.field_project_id == project_id,
            FieldImportRow.field_import_run_id == run_id,
        )
        .order_by(FieldImportRow.source_row_number)
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldImportRowPublic.model_validate(r) for r in rows]


async def list_findings_for_run(
    session: AsyncSession,
    user: User,
    project_id: int,
    run_id: int,
) -> list[FieldFindingPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)
    await _get_run_in_project(session, project_id, run_id)

    stmt = (
        select(FieldFinding)
        .where(
            FieldFinding.field_project_id == project_id,
            FieldFinding.field_import_run_id == run_id,
        )
        .order_by(FieldFinding.id)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldFindingPublic.model_validate(r) for r in rows]


async def list_ledger_events_for_project(
    session: AsyncSession,
    user: User,
    project_id: int,
    limit: int = 100,
) -> list[FieldLedgerEventPublic]:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)

    stmt = (
        select(FieldLedgerEvent)
        .where(FieldLedgerEvent.field_project_id == project_id)
        .order_by(FieldLedgerEvent.created_at.desc())
        .limit(min(max(limit, 1), 500))
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldLedgerEventPublic.model_validate(r) for r in rows]
