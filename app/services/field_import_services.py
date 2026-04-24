"""Importación CSV Field (2026.1) + Execution Ledger: filas, hallazgos, eventos."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_decision_model import SOURCE_TYPE_CSV
from app.models.field_ledger_model import FieldFinding, FieldImportRow, FieldLedgerEvent
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

OPTIONAL_COLUMNS = frozenset({"quota_cell", "lat", "lon", "flags"})

EVENT_IMPORT_STARTED = "import_started"
EVENT_IMPORT_FAILED = "import_failed"
EVENT_IMPORT_COMPLETED = "import_completed"

FINDING_DUPLICATE_CASE = "DUPLICATE_CASE_IN_RUN"
FINDING_INVALID_DURATION = "INVALID_DURATION"
FINDING_ROW_INCOMPLETE = "ROW_INCOMPLETE"


def _utc_naive() -> datetime:
    """UTC sin tzinfo: columnas TIMESTAMP WITHOUT TIME ZONE (asyncpg + aware falla)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_headers(fieldnames: list[str] | None) -> set[str]:
    if not fieldnames:
        return set()
    return {h.strip().lstrip("\ufeff").lower() for h in fieldnames if h and h.strip()}


def _cell(row: dict[str, Any], key: str) -> str:
    v = row.get(key)
    if v is None:
        return ""
    return str(v).strip()


def _cell_ci(row: dict[str, Any], key_lower: str) -> str:
    for k, v in row.items():
        if (k or "").strip().lower() == key_lower:
            return str(v).strip() if v is not None else ""
    return ""


def _extras_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    lower_map = {(k or "").strip().lower(): k for k in row.keys() if k}
    out: dict[str, Any] = {}
    for want in OPTIONAL_COLUMNS:
        orig = lower_map.get(want.lower())
        if orig:
            v = _cell(row, orig)
            if v:
                out[want] = v
    return out or None


def _parse_duration_sec(raw: str) -> tuple[int | None, bool]:
    """(valor, inválido)."""
    s = (raw or "").strip()
    if not s:
        return None, False
    try:
        n = int(float(s))
        if n < 0:
            return n, True
        return n, False
    except ValueError:
        return None, True


def _finding_message_row_incomplete(
    data_row_index: int, case_id: str, wave_id: str
) -> str:
    """Texto orientado a negocio / agencia (qué falta y qué hacer)."""
    missing: list[str] = []
    if not case_id:
        missing.append("«case_id» (código del caso en terreno)")
    if not wave_id:
        missing.append("«wave_id» (ola, semana o marco del levantamiento)")
    if len(missing) == 2:
        detail = " faltan " + " y ".join(missing)
    else:
        detail = " falta " + missing[0]
    return (
        f"Fila {data_row_index} del archivo (la fila 1 es la cabecera):{detail}. "
        "Sin esos dos datos el sistema no puede registrar el caso en el proyecto. "
        "Revise celdas vacías, espacios de más o un delimitador CSV mal configurado."
    )


def _finding_message_duplicate(
    case_id: str, wave_id: str, first_materialized_row_id: int
) -> str:
    return (
        f"Esta fila vuelve a usar el mismo caso y la misma ola que ya importó antes "
        f"(«{case_id}» + «{wave_id}»). La primera aparición quedó en el registro de fila id={first_materialized_row_id}. "
        "Si no era intencional, corrija el CSV; si son dos visitas distintas, use otro identificador de caso u ola."
    )


def _finding_message_invalid_duration(dur_raw: str) -> str:
    return (
        f"La duración en segundos no es válida: valor recibido «{dur_raw}». "
        "Debe ser un número entero mayor o igual que cero (sin letras ni símbolos). "
        "Si aún no tiene duración, deje la celda vacía."
    )


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


def _add_ledger_event(
    session: AsyncSession,
    *,
    project_id: int,
    run_id: int | None,
    actor_user_id: int | None,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> None:
    session.add(
        FieldLedgerEvent(
            field_project_id=project_id,
            field_import_run_id=run_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            payload=payload,
        )
    )


async def import_field_csv_2026_1(
    session: AsyncSession,
    user: User,
    project_id: int,
    raw_bytes: bytes,
) -> FieldImportRun:
    await assert_field_staff(user)
    project = await _get_project(session, project_id)
    _assert_project_access(user, project)

    actor_id: int | None = user.id if getattr(user, "id", None) else None

    run = FieldImportRun(
        field_project_id=project.id,
        status="processing",
        format_version=FORMAT_VERSION,
        error_detail=None,
        row_count=None,
    )
    session.add(run)
    await session.flush()

    _add_ledger_event(
        session,
        project_id=project.id,
        run_id=run.id,
        actor_user_id=actor_id,
        event_type=EVENT_IMPORT_STARTED,
        payload={"format_version": FORMAT_VERSION},
    )
    await session.flush()

    def fail(msg: str) -> FieldImportRun:
        run.status = "failed"
        run.error_detail = msg[:8000]
        run.row_count = None
        run.completed_at = _utc_naive()
        _add_ledger_event(
            session,
            project_id=project.id,
            run_id=run.id,
            actor_user_id=actor_id,
            event_type=EVENT_IMPORT_FAILED,
            payload={"detail": msg[:2000]},
        )
        return run

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

    seen_case_wave: dict[tuple[str, str], int] = {}
    data_row_index = 0
    finding_count = 0
    inserted_rows = 0

    for raw_row in reader:
        if not raw_row:
            continue
        values = [str(v).strip() if v is not None else "" for v in raw_row.values()]
        if not any(values):
            continue

        data_row_index += 1
        case_id = _cell_ci(raw_row, "case_id")
        wave_id = _cell_ci(raw_row, "wave_id")
        interviewer_id = _cell_ci(raw_row, "interviewer_id")
        disposition = _cell_ci(raw_row, "disposition")
        started_at = _cell_ci(raw_row, "started_at") or None
        completed_at = _cell_ci(raw_row, "completed_at") or None
        dur_raw = _cell_ci(raw_row, "duration_sec")
        duration_sec, dur_bad = _parse_duration_sec(dur_raw)

        if not case_id or not wave_id:
            finding_count += 1
            session.add(
                FieldFinding(
                    field_project_id=project.id,
                    field_import_run_id=run.id,
                    field_import_row_id=None,
                    code=FINDING_ROW_INCOMPLETE,
                    severity="error",
                    case_id=case_id or None,
                    wave_id=wave_id or None,
                    message=_finding_message_row_incomplete(
                        data_row_index, case_id, wave_id
                    ),
                    source=SOURCE_TYPE_CSV,
                )
            )
            continue

        extras = _extras_from_row(raw_row)

        db_row = FieldImportRow(
            field_project_id=project.id,
            field_import_run_id=run.id,
            source_row_number=data_row_index,
            case_id=case_id,
            wave_id=wave_id,
            interviewer_id=interviewer_id or "",
            disposition=disposition or "",
            started_at_text=started_at,
            completed_at_text=completed_at,
            duration_sec=duration_sec,
            extras=extras,
        )
        session.add(db_row)
        await session.flush()
        inserted_rows += 1

        key = (case_id.lower(), wave_id.lower())
        if key in seen_case_wave:
            finding_count += 1
            session.add(
                FieldFinding(
                    field_project_id=project.id,
                    field_import_run_id=run.id,
                    field_import_row_id=db_row.id,
                    code=FINDING_DUPLICATE_CASE,
                    severity="warn",
                    case_id=case_id,
                    wave_id=wave_id,
                    message=_finding_message_duplicate(
                        case_id, wave_id, seen_case_wave[key]
                    ),
                    source=SOURCE_TYPE_CSV,
                )
            )
        else:
            seen_case_wave[key] = db_row.id

        if dur_bad:
            finding_count += 1
            session.add(
                FieldFinding(
                    field_project_id=project.id,
                    field_import_run_id=run.id,
                    field_import_row_id=db_row.id,
                    code=FINDING_INVALID_DURATION,
                    severity="warn",
                    case_id=case_id,
                    wave_id=wave_id,
                    message=_finding_message_invalid_duration(dur_raw),
                    source=SOURCE_TYPE_CSV,
                )
            )

    run.status = "completed"
    run.row_count = inserted_rows
    run.error_detail = None
    run.completed_at = _utc_naive()

    _add_ledger_event(
        session,
        project_id=project.id,
        run_id=run.id,
        actor_user_id=actor_id,
        event_type=EVENT_IMPORT_COMPLETED,
        payload={
            "rows_materialized": inserted_rows,
            "data_lines_seen": data_row_index,
            "findings_created": finding_count,
        },
    )

    await session.commit()
    await session.refresh(run)
    return run
