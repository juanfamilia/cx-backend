"""
Cliente SurveyToGo (Dooblo) newapi: HTTP Basic hacia el host configurado
(globl `DOOBLO_*` o credenciales por empresa en `company_dooblo_settings`).

Nombres de parámetros: deben coincidir con la newapi; si 400 upstream, validar
con SurveyToGo REST API Testbed o soporte Dooblo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

_DEFAULT_TIMEOUT = 120.0


@dataclass(frozen=True, slots=True)
class DoobloCreds:
    base_url: str
    user: str
    password: str


def dooblo_configured() -> bool:
    """Solo comprobar si existen variables de entorno (fallback servidor)."""
    return creds_from_settings() is not None


def creds_from_settings() -> DoobloCreds | None:
    base = (settings.DOOBLO_BASE_URL or "").strip()
    u = (settings.DOOBLO_USER or "").strip()
    p = (settings.DOOBLO_PASSWORD or "").strip()
    if not base or not u or not p:
        return None
    return DoobloCreds(base_url=base.rstrip("/"), user=u, password=p)


def _creds_effective(override: DoobloCreds | None) -> DoobloCreds:
    c = override or creds_from_settings()
    if c is None:
        raise RuntimeError("Dooblo: sin credenciales (configurar por empresa o DOOBLO_* en servidor).")
    return c


def _base_for(creds: DoobloCreds) -> str:
    return creds.base_url.strip().rstrip("/")


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
    creds: DoobloCreds | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    """
    GET `/{operation}` con query limpia y Basic auth.
    `operation` sin slashes (ej. SurveyInterviewIDs).
    """
    c = _creds_effective(creds)
    op = operation.strip().lstrip("/").replace("..", "")
    if not op:
        raise ValueError("operation vacío")
    url = f"{_base_for(c)}/{op}"
    q = _clean_params(params)
    headers = {**(extra_headers or {})}
    async with httpx.AsyncClient() as client:
        return await client.get(
            url,
            params=q,
            headers=headers,
            auth=(c.user, c.password),
            timeout=timeout,
        )


async def get_survey_interview_ids(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("SurveyInterviewIDs", {"surveyIDs": survey_id}, creds=creds, timeout=timeout)


async def get_survey_interview_ids_by_last_modified(
    survey_id: str,
    *,
    days_back: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    creds: DoobloCreds | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    p: dict[str, Any] = {"surveyIDs": survey_id}
    if days_back is not None:
        p["daysBack"] = days_back
    if from_date is not None:
        p["fromDate"] = from_date
    if to_date is not None:
        p["toDate"] = to_date
    return await dooblo_get("SurveyInterviewIDsByLastModified", p, creds=creds, timeout=timeout)


async def get_project_surveys(
    project_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("ProjectSurveys", {"ProjectID": project_id}, creds=creds, timeout=timeout)


async def get_survey_details(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("Surveys", {"SurveyID": survey_id}, creds=creds, timeout=timeout)


async def get_simple_survey_export(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("SimpleSurveyExport", {"SurveyID": survey_id}, creds=creds, timeout=timeout)


async def get_simple_export(
    survey_id: str,
    subject_ids: str,
    *,
    creds: DoobloCreds | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    return await dooblo_get(
        "SimpleExport",
        {"SurveyID": survey_id, "subjectIDs": subject_ids},
        creds=creds,
        timeout=timeout,
    )


async def get_operation_data(
    survey_id: str,
    subject_ids: str,
    *,
    creds: DoobloCreds | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
    return await dooblo_get(
        "OperationData",
        {"SurveyID": survey_id, "subjectIDs": subject_ids},
        creds=creds,
        timeout=timeout,
    )


async def get_survey_interview_data(
    survey_id: str,
    subject_ids: str,
    *,
    only_headers: bool = False,
    include_nulls: bool = False,
    creds: DoobloCreds | None = None,
    timeout: float = 180.0,
) -> httpx.Response:
    return await dooblo_get(
        "SurveyInterviewData",
        {
            "surveyID": survey_id,
            "subjectIDs": subject_ids,
            "onlyHeaders": only_headers,
            "includeNulls": include_nulls,
        },
        creds=creds,
        extra_headers={"Accept": "text/xml, application/json;q=0.9, */*;q=0.8"},
        timeout=timeout,
    )


async def get_survey_quotas_status(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("GetSurveyQuotasStatus", {"SurveyID": survey_id}, creds=creds, timeout=timeout)


async def get_quota_structure(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("QuotaStructure", {"SurveyID": survey_id}, creds=creds, timeout=timeout)


async def get_handling_examples(
    survey_id: str, *, creds: DoobloCreds | None = None, timeout: float = _DEFAULT_TIMEOUT
) -> httpx.Response:
    return await dooblo_get("HandlingExamples", {"SurveyID": survey_id}, creds=creds, timeout=timeout)


async def get_surveyors_route(
    *,
    survey_id: str | None = None,
    surveyor_name: str | None = None,
    group_name: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    creds: DoobloCreds | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> httpx.Response:
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
    return await dooblo_get("GetSurveyorsRoute", p, creds=creds, timeout=timeout)
