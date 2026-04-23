"""
Cliente SurveyToGo (Dooblo) newapi: HTTP Basic hacia https://api.dooblo.net/newapi

Todas las operaciones de documentación Dooblo comparten el mismo patrón:
GET/POST a `/{OperationName}` con query / body según el Testbed oficial.

Nombres de parámetros: deben coincidir con la newapi; si 400 upstream, validar
con SurveyToGo REST API Testbed o soporte Dooblo.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

_DEFAULT_TIMEOUT = 120.0


def dooblo_configured() -> bool:
    return bool(
        (settings.DOOBLO_BASE_URL or "").strip()
        and (settings.DOOBLO_USER or "").strip()
        and (settings.DOOBLO_PASSWORD or "").strip()
    )


def _require_config() -> None:
    if not dooblo_configured():
        raise RuntimeError("Dooblo: faltan DOOBLO_BASE_URL, DOOBLO_USER o DOOBLO_PASSWORD")


def _base() -> str:
    _require_config()
    return (settings.DOOBLO_BASE_URL or "").strip().rstrip("/")


def _clean_params(
    params: dict[str, Any] | None,
) -> dict[str, str] | None:
    if not params:
        return None
    out: dict[str, str] = {}
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        else:
            out[k] = str(v)
    return out or None


async def dooblo_get(
    operation: str,
    params: dict[str, Any] | None = None,
    *,
    extra_headers: dict[str, str] | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    """
    GET `/{operation}` con query limpia y Basic auth.
    `operation` sin slashes (ej. SurveyInterviewIDs).
    """
    _require_config()
    assert settings.DOOBLO_USER is not None
    assert settings.DOOBLO_PASSWORD is not None
    op = operation.strip().lstrip("/").replace("..", "")
    if not op:
        raise ValueError("operation vacío")
    url = f"{_base()}/{op}"
    q = _clean_params(params)
    headers = {**(extra_headers or {})}
    async with httpx.AsyncClient() as client:
        return await client.get(
            url,
            params=q,
            headers=headers,
            auth=(settings.DOOBLO_USER, settings.DOOBLO_PASSWORD),
            timeout=timeout,
        )


# --- Operaciones usadas por Field (prioridad 1) ---


async def get_survey_interview_ids(survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    """GET SurveyInterviewIDs — lista IDs; parámetro típico surveyIDs."""
    return await dooblo_get("SurveyInterviewIDs", {"surveyIDs": survey_id}, timeout=timeout)


async def get_survey_interview_ids_by_last_modified(
    survey_id: str,
    *,
    days_back: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    """
    SurveyInterviewIDsByLastModified.
    Ajuste de claves: Dooblo puede usar distintas; se pasan las más habituales.
    """
    p: dict[str, Any] = {"surveyIDs": survey_id}
    if days_back is not None:
        p["daysBack"] = days_back
    if from_date is not None:
        p["fromDate"] = from_date
    if to_date is not None:
        p["toDate"] = to_date
    return await dooblo_get("SurveyInterviewIDsByLastModified", p, timeout=timeout)


async def get_project_surveys(project_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    """Encuestas dentro de un proyecto."""
    return await dooblo_get("ProjectSurveys", {"ProjectID": project_id}, timeout=timeout)


async def get_survey_details(survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    """Detalle de encuesta (operación Surveys en doc Dooblo)."""
    return await dooblo_get("Surveys", {"SurveyID": survey_id}, timeout=timeout)


async def get_simple_survey_export(
    survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    """SimpleSurveyExport — estructura de encuesta (JSON o XML según newapi / headers)."""
    return await dooblo_get("SimpleSurveyExport", {"SurveyID": survey_id}, timeout=timeout)


async def get_simple_export(
    survey_id: str,
    subject_ids: str,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    """
    SimpleExport (tipo Excel) — subjectIDs en texto, ej. 1,2,3.
    """
    return await dooblo_get(
        "SimpleExport",
        {"SurveyID": survey_id, "subjectIDs": subject_ids},
        timeout=timeout,
    )


async def get_operation_data(
    survey_id: str,
    subject_ids: str,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    return await dooblo_get(
        "OperationData",
        {"SurveyID": survey_id, "subjectIDs": subject_ids},
        timeout=timeout,
    )


async def get_survey_interview_data(
    survey_id: str,
    subject_ids: str,
    *,
    only_headers: bool = False,
    include_nulls: bool = False,
    timeout: float = 180.0,
) -> httpx.Response:
    """
    Cuerpos de entrevista; Dooblo suele devolver XML. Máx. 99 ID por request.
    """
    return await dooblo_get(
        "SurveyInterviewData",
        {
            "surveyID": survey_id,
            "subjectIDs": subject_ids,
            "onlyHeaders": only_headers,
            "includeNulls": include_nulls,
        },
        extra_headers={"Accept": "text/xml, application/json;q=0.9, */*;q=0.8"},
        timeout=timeout,
    )


# --- Cuota y GPS (Field: alertas, no reemplazar Studio) ---


async def get_survey_quotas_status(survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    return await dooblo_get("GetSurveyQuotasStatus", {"SurveyID": survey_id}, timeout=timeout)


async def get_quota_structure(survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    return await dooblo_get("QuotaStructure", {"SurveyID": survey_id}, timeout=timeout)


async def get_handling_examples(survey_id: str, *, timeout: float = _DEFAULT_TIMEOUT) -> httpx.Response:
    return await dooblo_get("HandlingExamples", {"SurveyID": survey_id}, timeout=timeout)


async def get_surveyors_route(
    *,
    survey_id: str | None = None,
    surveyor_name: str | None = None,
    group_name: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    """
    GetSurveyorsRoute (doc: un nombre de encuestado o de grupo, según API).
    """
    p: dict[str, Any] = {}
    if survey_id is not None:
        p["SurveyID"] = survey_id
    if surveyor_name is not None:
        p["SurveyorName"] = surveyor_name
    if group_name is not None:
        p["GroupName"] = group_name
    if from_date is not None:
        p["fromDate"] = from_date
    if to_date is not None:
        p["toDate"] = to_date
    if not p.get("SurveyorName") and not p.get("GroupName"):
        raise ValueError("GetSurveyorsRoute requiere SurveyorName o GroupName (según documentación).")
    return await dooblo_get("GetSurveyorsRoute", p, timeout=timeout)
