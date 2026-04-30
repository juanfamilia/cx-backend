"""
Motor de reglas Field Execution Control (Layer 2): señales Dooblo + política → hallazgos.

Extensible sin acoplar a un solo XML/JSON upstream. Los códigos viven en
``field_finding_codes`` (contrato §3.2 arquitectura). El pipeline de análisis async
debe pasar por ``collect_dooblo_analysis_finding_drafts`` para sumar reglas sin
duplicar orden ni idempotencia.
"""

from __future__ import annotations

import math
from typing import Any, TypedDict

from app.integrations.field_finding_codes import (
    DOOBLO_NO_SURVEY_ID,
    DOOBLO_QUOTA_SNAPSHOT,
    DOOBLO_QUOTA_UPSTREAM,
    QUOTA_MAX_DEVIATION,
)


class FindingDraft(TypedDict, total=False):
    code: str
    severity: str
    message: str
    idempotency_key: str
    explanation: str
    recommendation: str
    evidence: dict[str, Any]


# Compatibilidad: imports antiguos desde este módulo
CODE_DOOBLO_QUOTA_OK = DOOBLO_QUOTA_SNAPSHOT
CODE_DOOBLO_QUOTA_ERROR = DOOBLO_QUOTA_UPSTREAM
CODE_QUOTA_DEVIATION = QUOTA_MAX_DEVIATION
CODE_NO_SURVEY = DOOBLO_NO_SURVEY_ID


def collect_dooblo_analysis_finding_drafts(
    *,
    upstream_status: int,
    quota_payload: Any,
    policy_config: dict[str, Any],
    sync_run_id: int,
) -> list[FindingDraft]:
    """
    Punto único de ensamble para la corrida ``field_analysis`` vía Dooblo.

    Hoy: cuota + desvío heurístico. Próximos builders (misma firma conceptual):
    muestral export / duración / straight-lining / GPS / roll-ups de riesgo —
    todos emiten ``FindingDraft`` con idempotency_key estable por sync_run.
    """
    return build_findings_from_quota_response(
        upstream_status=upstream_status,
        quota_payload=quota_payload,
        policy_config=policy_config,
        sync_run_id=sync_run_id,
    )


def _iter_numbers(obj: Any) -> list[float]:
    """Hojea listas/dicts y extrae números para heurística de desvío (MVP)."""
    out: list[float] = []
    if obj is None:
        return out
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        f = float(obj)
        if not math.isnan(f) and not math.isinf(f):
            out.append(f)
        return out
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(_iter_numbers(v))
    if isinstance(obj, (list, tuple)):
        for v in obj:
            out.extend(_iter_numbers(v))
    return out


def build_findings_from_quota_response(
    *,
    upstream_status: int,
    quota_payload: Any,
    policy_config: dict[str, Any],
    sync_run_id: int,
) -> list[FindingDraft]:
    """
    Construye hallazgos a partir de GetSurveyQuotasStatus (o proxy serializado) + umbrales.
    Si el JSON upstream no trae pares (target/actual) reconocibles, aún deja
    rastro informativo de captura o error HTTP.
    """
    base = f"dec:sync{sync_run_id}"
    out: list[FindingDraft] = []

    if upstream_status is None or not (200 <= int(upstream_status) < 300):
        out.append(
            {
                "code": CODE_DOOBLO_QUOTA_ERROR,
                "severity": "error",
                "message": f"Dooblo devolvió estado HTTP {upstream_status} al consultar cuota.",
                # Sufijo estable (histórico) — no cambiar sin migración de idempotencia
                "idempotency_key": f"{base}:CODE_DOOBLO_QUOTA_ERROR",
                "explanation": "No se pudo leer el estado de cuota en SurveyToGo; el análisis no sustituye control manual.",
                "recommendation": "Revisar credenciales, survey ID, permisos o disponibilidad del API.",
                "evidence": {"upstream_status": upstream_status},
            }
        )
        return out

    # Sin error HTTP: al menos informar que hubo captura
    out.append(
        {
            "code": CODE_DOOBLO_QUOTA_OK,
            "severity": "info",
            "message": "Estado de cuota recibido desde Dooblo; compare con el plan de muestreo del estudio.",
            "idempotency_key": f"{base}:CODE_DOOBLO_QUOTA_OK",
            "explanation": "Snapshot almacenado; la forma exacta del JSON depende de la encuesta (Documentación Dooblo / Testbed).",
            "recommendation": "Ajuste `quota_max_deviation_pct` en la política cuando tenga fórmula de negocio fijada con el mandante.",
            "evidence": {"payload_shape": _shape_hint(quota_payload)},
        }
    )

    max_pct = policy_config.get("quota_max_deviation_pct")
    if max_pct is None:
        return out

    try:
        threshold = float(max_pct)
    except (TypeError, ValueError):
        return out

    # Heurística: buscar pares aproximados (target, actual) o ratios en números sueltos
    nums = _iter_numbers(quota_payload)
    if not nums:
        return out

    # MVP: desviación = ((max - min) / (max+eps)) * 100 si hay al menos 2 números
    if len(nums) >= 2:
        lo, hi = min(nums), max(nums)
        span = abs(hi - lo)
        denom = max(abs(hi), 1.0)
        approx_pct = (span / denom) * 100.0
        if approx_pct > threshold + 0.0001:
            out.append(
                {
                    "code": CODE_QUOTA_DEVIATION,
                    "severity": "warn" if approx_pct < threshold * 1.5 else "error",
                    "message": f"Señal de dispersión en métricas de cuota (heurística ~{approx_pct:.1f}%) frente a umbral {threshold}%.",
                    "idempotency_key": f"{base}:CODE_QUOTA_DEVIATION",
                    "explanation": "Cálculo aproximado a partir de valores numéricos en la respuesta; no sustituye definición de celda/negocio por el estudio.",
                    "recommendation": "Cruce con plan de muestreo; refine reglas o importe criterios de celda en versiones de política.",
                    "evidence": {
                        "approx_dispersion_pct": round(approx_pct, 3),
                        "threshold_pct": threshold,
                    },
                }
            )

    return out


def _shape_hint(p: Any) -> str:
    if p is None:
        return "null"
    if isinstance(p, dict):
        return f"dict({len(p)} keys)"
    if isinstance(p, list):
        return f"list(len={len(p)})"
    return type(p).__name__
