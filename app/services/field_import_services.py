"""Importación CSV Field (formato 2026.1) — validación + field_import_runs (sin staging aún)."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.field_project_model import FieldImportRun, FieldProject
from app.models.user_model import User
from app.services.field_project_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException

FORMAT_VERSION = "2026.1"

REQUIRED_COLUMNS = frozenset(
    {
        "case_id",
        "wave_id",
        "interviewer_id",
        "disposition",
        "started_at",
        "completed_at",
        "duration_sec",
    }
)


def _normalize_headers(fieldnames: list[str] | None) -> set[str]:
    if not fieldnames:
        return set()
    return {h.strip().lstrip("\ufeff") for h in fieldnames if h and h.strip()}


async def _get_project(session: AsyncSession, project_id: int) -> FieldProject:
    row = await session.get(FieldProject, project_id)
    if row is None or row.deleted_at is not None:
        raise NotFoundException("Proyecto Field no encontrado")
    return row


def _assert_project_access(user: User, project: FieldProject) -> None:
    if user.role == 0:
        return
    if user.company_id is None or project.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="proyecto Field no permitido")


async def import_field_csv_2026_1(
    session: AsyncSession,
    user: User,
    project_id: int,
    raw_bytes: bytes,
) -> FieldImportRun:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)

    run = FieldImportRun(
        field_project_id=project.id,
        status="processing",
        format_version=FORMAT_VERSION,
        error_detail=None,
        row_count=None,
    )
    session.add(run)
    await session.flush()

    def fail(msg: str) -> None:
        run.status = "failed"
        run.error_detail = msg[:8000]
        run.row_count = None
        run.completed_at = datetime.now(timezone.utc)

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        fail(f"CSV no es UTF-8 válido: {e}")
        await session.commit()
        await session.refresh(run)
        return run

    reader = csv.DictReader(io.StringIO(text))
    headers = _normalize_headers(reader.fieldnames)
    missing = REQUIRED_COLUMNS - headers
    if missing:
        fail(f"Cabeceras inválidas. Faltan columnas: {', '.join(sorted(missing))}")
        await session.commit()
        await session.refresh(run)
        return run

    row_count = 0
    for row in reader:
        if not row:
            continue
        values = [str(v).strip() if v is not None else "" for v in row.values()]
        if not any(values):
            continue
        row_count += 1

    run.status = "completed"
    run.row_count = row_count
    run.error_detail = None
    run.completed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(run)
    return run
