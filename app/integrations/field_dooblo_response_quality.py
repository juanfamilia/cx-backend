"""
Señales de calidad sobre datos de respuesta Dooblo (OperationData / JSON tabular).

Sin XML pesado en v1: si upstream devuelve XML u forma no reconocida, no emitimos
falsos positivos; solo trazamos forma del payload en evidencia agregada.

Umbrales vía ``FieldPolicySet.config`` (JSON), p.ej.::

    response_quality_enabled: true   # activa muestra tabular + duración / straight-lining (opt-in)
    gps_quality_enabled: true        # misma muestra: columnas lat/lon en export (opt-in)
    dooblo_tabular_max_subjects: 30  # opcional; si omite, usa response_quality_max_subjects
    response_quality_max_subjects: 30
    interview_duration_seconds_min: 45
    interview_duration_seconds_max: 3600
    straight_lining_enabled: true
    straight_lining_min_numeric_cells: 8
    straight_lining_scale_min: 1
    straight_lining_scale_max: 5
"""

from __future__ import annotations

import math
import re
from typing import Any

_SUBJECT_ID_KEYS = frozenset(
    k.lower()
    for k in (
        "SubjectID",
        "subjectID",
        "subjectId",
        "InterviewId",
        "interviewId",
        "ID",
        "Id",
        "SubjectId",
    )
)

_DURATION_KEY_HINTS = (
    "duration",
    "duracion",
    "seconds",
    "length",
    "interviewlength",
    "totaltimesec",
    "totaltime",
)


def extract_subject_ids_from_survey_interview_payload(data: Any, *, max_ids: int = 500) -> list[str]:
    """Interpreta JSON típico de SurveyInterviewIDs (listas anidadas o dicts heterogéneos)."""
    seen: list[str] = []
    found: set[str] = set()

    def push(x: Any) -> None:
        if len(seen) >= max_ids:
            return
        if x is None:
            return
        if isinstance(x, bool):
            return
        if isinstance(x, int) and not isinstance(x, bool):
            s = str(x)
            if s not in found:
                found.add(s)
                seen.append(s)
            return
        if isinstance(x, float) and x == int(x):
            s = str(int(x))
            if s not in found:
                found.add(s)
                seen.append(s)
            return
        if isinstance(x, str):
            for part in re.split(r"[,\s;]+", x.strip()):
                t = part.strip()
                if len(t) < 2:
                    continue
                if t not in found:
                    found.add(t)
                    seen.append(t)
            return

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for k, v in item.items():
                    if str(k).lower() in _SUBJECT_ID_KEYS:
                        if isinstance(v, (list, tuple)):
                            for it in v:
                                push(it)
                        else:
                            push(v)
            else:
                push(item)
        return seen[:max_ids]

    def walk(obj: Any) -> None:
        if len(seen) >= max_ids:
            return
        if obj is None:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = str(k).lower()
                if lk in _SUBJECT_ID_KEYS:
                    if isinstance(v, (list, tuple)):
                        for it in v:
                            push(it)
                    else:
                        push(v)
                elif isinstance(v, (dict, list, tuple)):
                    walk(v)
            return
        if isinstance(obj, (list, tuple)):
            for item in obj:
                walk(item)

    walk(data)
    return seen[:max_ids]


def flatten_tabular_rows(payload: Any) -> list[dict[str, Any]]:
    """
    Convierte OperationData / SimpleExport JSON en filas dict(str -> valor escalar).
    Acepta lista de dicts, dict con lista bajo claves comunes, o una sola fila dict.
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                rows.append({str(k): v for k, v in item.items()})
        return rows
    if isinstance(payload, dict):
        for key in (
            "Rows",
            "rows",
            "Data",
            "data",
            "Items",
            "items",
            "Subjects",
            "subjects",
            "Interviews",
            "interviews",
            "Result",
            "result",
        ):
            inner = payload.get(key)
            if isinstance(inner, list):
                return flatten_tabular_rows(inner)
        if any(not isinstance(v, (dict, list)) for v in payload.values()):
            return [{str(k): v for k, v in payload.items()}]
    return []


def _cell_as_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    if isinstance(v, str):
        t = v.strip().replace(",", ".")
        if not t:
            return None
        try:
            return float(t)
        except ValueError:
            return None
    return None


def extract_duration_seconds(row: dict[str, Any]) -> float | None:
    """Primera celda que parezca duración en segundos (clave o magnitud razonable)."""
    best: float | None = None
    for key, raw in row.items():
        lk = str(key).lower().replace(" ", "")
        val = _cell_as_float(raw)
        if val is None:
            continue
        if any(h in lk for h in _DURATION_KEY_HINTS):
            if val > 86400 * 7:
                continue
            return val
        if best is None and 5 <= val <= 86400:
            best = val
    return best


def likert_like_values(
    row: dict[str, Any],
    *,
    scale_min: float,
    scale_max: float,
    min_cells: int,
) -> list[float]:
    vals: list[float] = []
    for key, raw in row.items():
        lk = str(key).lower().replace(" ", "")
        if lk.startswith("_"):
            continue
        if lk in ("id", "caseid", "case_id", "subjectid", "interviewid"):
            continue
        if any(h in lk for h in _DURATION_KEY_HINTS):
            continue
        if lk.endswith("id") and "grid" not in lk:
            continue
        v = _cell_as_float(raw)
        if v is None:
            continue
        if scale_min <= v <= scale_max and abs(v - round(v)) < 1e-6:
            vals.append(v)
    return vals if len(vals) >= min_cells else []


def summarize_response_quality_rows(
    rows: list[dict[str, Any]],
    *,
    duration_min: float | None,
    duration_max: float | None,
    straight_enabled: bool,
    scale_min: float,
    scale_max: float,
    straight_min_cells: int,
) -> dict[str, Any]:
    n = len(rows)
    dur_too_short = 0
    dur_too_long = 0
    dur_missing = 0
    straight_hits = 0
    sample_durations: list[float] = []

    for row in rows:
        d = extract_duration_seconds(row)
        if d is None:
            dur_missing += 1
        else:
            sample_durations.append(d)
            if duration_min is not None and d < duration_min:
                dur_too_short += 1
            if duration_max is not None and d > duration_max:
                dur_too_long += 1

        if straight_enabled:
            cells = likert_like_values(
                row,
                scale_min=scale_min,
                scale_max=scale_max,
                min_cells=straight_min_cells,
            )
            if len(cells) >= straight_min_cells and len({round(c, 3) for c in cells}) == 1:
                straight_hits += 1

    return {
        "row_count": n,
        "duration_too_short": dur_too_short,
        "duration_too_long": dur_too_long,
        "duration_missing": dur_missing,
        "straight_lining_rows": straight_hits,
        "duration_sample": sample_durations[:12],
    }


def duration_bounds_from_policy(policy_config: dict[str, Any]) -> tuple[float | None, float | None]:
    """Si checks activos, (min_sec, max_sec); si no, (None, None) — sin aplicar umbrales."""
    if policy_config.get("interview_duration_check_enabled", True) is False:
        return None, None
    lo = policy_config.get("interview_duration_seconds_min", 45)
    hi = policy_config.get("interview_duration_seconds_max", 7200)
    try:
        return float(lo), float(hi)
    except (TypeError, ValueError):
        return 45.0, 7200.0


def straight_lining_params_from_policy(policy_config: dict[str, Any]) -> tuple[bool, float, float, int]:
    enabled = policy_config.get("straight_lining_enabled", True) is not False
    smin = policy_config.get("straight_lining_scale_min", 1)
    smax = policy_config.get("straight_lining_scale_max", 5)
    cells = policy_config.get("straight_lining_min_numeric_cells", 8)
    try:
        return enabled, float(smin), float(smax), max(3, int(cells))
    except (TypeError, ValueError):
        return enabled, 1.0, 5.0, 8
