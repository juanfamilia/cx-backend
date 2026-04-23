"""
Cliente SurveyToGo (Dooblo) newapi: HTTP Basic hacia https://api.dooblo.net/newapi

Uso: Field u otros módulos; nunca exponer credenciales al front.
"""

from __future__ import annotations

import httpx

from app.core.config import settings


def dooblo_configured() -> bool:
    return bool(
        (settings.DOOBLO_BASE_URL or "").strip()
        and (settings.DOOBLO_USER or "").strip()
        and (settings.DOOBLO_PASSWORD or "").strip()
    )


def _base() -> str:
    if not dooblo_configured():
        raise RuntimeError("Dooblo: faltan DOOBLO_BASE_URL, DOOBLO_USER o DOOBLO_PASSWORD")
    return (settings.DOOBLO_BASE_URL or "").strip().rstrip("/")


async def get_survey_interview_ids(
    survey_id: str,
    *,
    timeout: float = 120.0,
    follow_redirects: bool = True,
) -> httpx.Response:
    """
    GET .../SurveyInterviewIDs?surveyIDs=<id>
    Autenticación: Basic (usuario típico REST_KEY/cuenta, contraseña de cuenta).
    """
    assert settings.DOOBLO_USER is not None
    assert settings.DOOBLO_PASSWORD is not None
    url = f"{_base()}/SurveyInterviewIDs"
    async with httpx.AsyncClient() as client:
        return await client.get(
            url,
            params={"surveyIDs": survey_id},
            auth=(settings.DOOBLO_USER, settings.DOOBLO_PASSWORD),
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
