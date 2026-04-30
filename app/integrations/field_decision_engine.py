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
    DOOBLO_GPS_NO_COORDINATES_IN_TABULAR,
    DOOBLO_NO_SURVEY_ID,
    DOOBLO_OPERATIONDATA_UPSTREAM,
    DOOBLO_QUOTA_SNAPSHOT,
    DOOBLO_QUOTA_UPSTREAM,
    DOOBLO_RESPONSE_QUALITY_EMPTY_SAMPLE,
    DOOBLO_RESPONSE_QUALITY_NO_TABULAR_ROWS,
    DOOBLO_SURVEY_INTERVIEW_IDS_UPSTREAM,
    FIELD_DURATION_ANOMALY,
    FIELD_GPS_INCONSISTENT,
    FIELD_STRAIGHT_LINING,
    QUOTA_MAX_DEVIATION,
)
from app.integrations.field_dooblo_response_quality import (
    duration_bounds_from_policy,
    straight_lining_params_from_policy,
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
    tabular_sample: dict[str, Any] | None = None,
) -> list[FindingDraft]:
    """
    Punto único de ensamble para la corrida ``field_analysis`` vía Dooblo.

    Cuota + (opcional) muestra tabular acotada para calidad de respuesta y/o GPS.
    ``tabular_sample`` requiere ``response_quality_enabled`` y/o ``gps_quality_enabled``.
    """
    quota_drafts = build_findings_from_quota_response(
        upstream_status=upstream_status,
        quota_payload=quota_payload,
        policy_config=policy_config,
        sync_run_id=sync_run_id,
    )
    rq_on = policy_config.get("response_quality_enabled", False)
    gps_on = policy_config.get("gps_quality_enabled", False)
    if not (rq_on or gps_on):
        return quota_drafts
    ts = tabular_sample or {}
    gate = _tabular_upstream_gate(rq=ts, sync_run_id=sync_run_id)
    if gate:
        return quota_drafts + gate
    row_drafts: list[FindingDraft] = []
    if rq_on:
        row_drafts.extend(_response_quality_row_findings(policy_config, sync_run_id, ts))
    if gps_on:
        row_drafts.extend(_gps_quality_row_findings(policy_config, sync_run_id, ts))
    return quota_drafts + row_drafts


def _tabular_upstream_gate(
    *,
    rq: dict[str, Any],
    sync_run_id: int,
) -> list[FindingDraft]:
    """Hallazgos terminales antes de heurísticas por fila (compartido respuesta + GPS)."""
    if not rq:
        return []
    base = f"dec:sync{sync_run_id}"
    iv_st = rq.get("interview_ids_status")
    op_st = rq.get("operation_status")
    sample_n = int(rq.get("subject_sample_size") or 0)
    summary = rq.get("summary") if isinstance(rq.get("summary"), dict) else {}
    row_count = int(summary.get("row_count") or 0)
    used_fb = bool(rq.get("used_simple_export_fallback"))

    if iv_st is not None and not (200 <= int(iv_st) < 300):
        return [
            {
                "code": DOOBLO_SURVEY_INTERVIEW_IDS_UPSTREAM,
                "severity": "warn",
                "message": f"SurveyToGo devolvió HTTP {iv_st} al listar IDs de entrevista para la muestra tabular.",
                "idempotency_key": f"{base}:{DOOBLO_SURVEY_INTERVIEW_IDS_UPSTREAM}",
                "explanation": "Sin IDs no se puede armar OperationData/SimpleExport acotado; cuota u otros hallazgos no tabulares siguen válidos.",
                "recommendation": "Revise permisos API, survey ID y límites Dooblo; desactive `response_quality_enabled` / `gps_quality_enabled` si no aplica.",
                "evidence": {"interview_ids_status": iv_st},
            }
        ]

    if sample_n == 0:
        return [
            {
                "code": DOOBLO_RESPONSE_QUALITY_EMPTY_SAMPLE,
                "severity": "info",
                "message": "No hay sujetos en el universo devuelto para el survey (muestra tabular vacía).",
                "idempotency_key": f"{base}:{DOOBLO_RESPONSE_QUALITY_EMPTY_SAMPLE}",
                "explanation": "SurveyInterviewIDs respondió OK pero sin IDs utilizables; no corren heurísticas tabulares en esta corrida.",
                "recommendation": "Confirme entrevistas completadas visibles para la cuenta API.",
                "evidence": {"interview_ids_status": iv_st},
            }
        ]

    if op_st is not None and not (200 <= int(op_st) < 300):
        return [
            {
                "code": DOOBLO_OPERATIONDATA_UPSTREAM,
                "severity": "warn",
                "message": f"SurveyToGo devolvió HTTP {op_st} al leer OperationData/SimpleExport para la muestra.",
                "idempotency_key": f"{base}:{DOOBLO_OPERATIONDATA_UPSTREAM}",
                "explanation": "No se pudieron analizar filas tabulares en esta corrida.",
                "recommendation": "Revise endpoint, tamaño de subjectIDs y formato (JSON vs XML).",
                "evidence": {
                    "operation_status": op_st,
                    "subject_sample_size": sample_n,
                    "used_simple_export_fallback": used_fb,
                },
            }
        ]

    if row_count == 0:
        return [
            {
                "code": DOOBLO_RESPONSE_QUALITY_NO_TABULAR_ROWS,
                "severity": "info",
                "message": "La respuesta no entregó filas tabulares reconocibles (puede ser XML u otro formato).",
                "idempotency_key": f"{base}:{DOOBLO_RESPONSE_QUALITY_NO_TABULAR_ROWS}",
                "explanation": "Sin tablas JSON no emitimos señales de superficie tabular para evitar falsos positivos.",
                "recommendation": "Verifique JSON tabular en OperationData/SimpleExport o amplíe el parser.",
                "evidence": {
                    "subject_sample_size": sample_n,
                    "used_simple_export_fallback": used_fb,
                    "simple_export_status": rq.get("simple_export_status"),
                },
            }
        ]

    return []


def _response_quality_row_findings(
    policy_config: dict[str, Any],
    sync_run_id: int,
    rq: dict[str, Any],
) -> list[FindingDraft]:
    summary = rq.get("summary") if isinstance(rq.get("summary"), dict) else {}
    row_count = int(summary.get("row_count") or 0)
    if row_count <= 0:
        return []

    def _f(x: Any) -> float | None:
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    warn_dur = _f(policy_config.get("duration_anomaly_warn_ratio"))
    err_dur = _f(policy_config.get("duration_anomaly_error_ratio"))
    warn_sl = _f(policy_config.get("straight_lining_warn_ratio"))
    err_sl = _f(policy_config.get("straight_lining_error_ratio"))
    warn_dur = 0.08 if warn_dur is None else warn_dur
    err_dur = 0.20 if err_dur is None else err_dur
    warn_sl = 0.08 if warn_sl is None else warn_sl
    err_sl = 0.18 if err_sl is None else err_sl

    base = f"dec:sync{sync_run_id}"
    out: list[FindingDraft] = []

    d_lo, d_hi = duration_bounds_from_policy(policy_config)
    duration_active = d_lo is not None or d_hi is not None
    if duration_active:
        short = int(summary.get("duration_too_short") or 0)
        long = int(summary.get("duration_too_long") or 0)
        anom = short + long
        if anom > 0:
            ratio = anom / row_count
            dur_sev: str | None = None
            if ratio >= err_dur:
                dur_sev = "error"
            elif ratio >= warn_dur:
                dur_sev = "warn"
            if dur_sev:
                out.append(
                    {
                        "code": FIELD_DURATION_ANOMALY,
                        "severity": dur_sev,
                        "message": (
                            f"{anom}/{row_count} casos en muestra con duración fuera del rango "
                            f"({d_lo}–{d_hi} s según política)."
                        ),
                        "idempotency_key": f"{base}:{FIELD_DURATION_ANOMALY}",
                        "explanation": "Heurística sobre columnas de duración detectadas en filas exportadas; no sustituye QC manual.",
                        "recommendation": "Revise entrevistas cortas/largas extremas; ajuste umbrales `interview_duration_seconds_*` si el diseño del survey lo requiere.",
                        "evidence": {
                            "row_count": row_count,
                            "duration_too_short": short,
                            "duration_too_long": long,
                            "ratio": round(ratio, 4),
                            "bounds": {"min": d_lo, "max": d_hi},
                        },
                    }
                )

    st_en, _, _, _ = straight_lining_params_from_policy(policy_config)
    if st_en:
        sl = int(summary.get("straight_lining_rows") or 0)
        if sl > 0:
            ratio = sl / row_count
            sl_sev: str | None = None
            if ratio >= err_sl:
                sl_sev = "error"
            elif ratio >= warn_sl:
                sl_sev = "warn"
            if sl_sev:
                out.append(
                    {
                        "code": FIELD_STRAIGHT_LINING,
                        "severity": sl_sev,
                        "message": f"{sl}/{row_count} filas con respuestas Likert homogéneas en bloque (straight lining).",
                        "idempotency_key": f"{base}:{FIELD_STRAIGHT_LINING}",
                        "explanation": "Se cuentan filas donde muchas celdas numéricas en escala comparten el mismo valor redondeado.",
                        "recommendation": "Valide con diseño de cuestionario y campo; refine `straight_lining_*` en política si hay grids válidos de respuesta única.",
                        "evidence": {
                            "row_count": row_count,
                            "straight_lining_rows": sl,
                            "ratio": round(ratio, 4),
                        },
                    }
                )

    return out


def _severity_from_ratio(ratio: float, *, warn_at: float, error_at: float) -> str | None:
    if ratio >= error_at:
        return "error"
    if ratio >= warn_at:
        return "warn"
    return None


def _worst_severity(a: str | None, b: str | None) -> str | None:
    rank = {"warn": 1, "error": 2}
    m = max(rank.get(a or "", 0), rank.get(b or "", 0))
    if m == 0:
        return None
    return "error" if m == 2 else "warn"


def _gps_quality_row_findings(
    policy_config: dict[str, Any],
    sync_run_id: int,
    rq: dict[str, Any],
) -> list[FindingDraft]:
    gsum = rq.get("gps_summary")
    if not isinstance(gsum, dict):
        return []
    base = f"dec:sync{sync_run_id}"
    row_count = int(gsum.get("row_count") or 0)
    wc = int(gsum.get("rows_with_coords") or 0)
    if row_count <= 0:
        return []

    if wc == 0:
        return [
            {
                "code": DOOBLO_GPS_NO_COORDINATES_IN_TABULAR,
                "severity": "info",
                "message": "Hay filas tabulares pero no se detectaron columnas lat/lon utilizables en la muestra.",
                "idempotency_key": f"{base}:{DOOBLO_GPS_NO_COORDINATES_IN_TABULAR}",
                "explanation": "Sin coordenadas exportadas no hay señal GPS de superficie; no se infieren ubicaciones.",
                "recommendation": "Revise nombres en el export; puede fijar ``gps_column_pairs`` en la política (lat/lon por encuesta).",
                "evidence": {"row_count": row_count},
            }
        ]

    def _fr(key: str, default_warn: float, default_err: float) -> tuple[float, float]:
        try:
            w = float(policy_config.get(f"{key}_warn_ratio", default_warn))
            e = float(policy_config.get(f"{key}_error_ratio", default_err))
            return w, e
        except (TypeError, ValueError):
            return default_warn, default_err

    iw_warn, iw_err = _fr("gps_invalid_coord", 0.08, 0.20)
    sp_warn, sp_err = _fr("gps_internal_span", 0.08, 0.18)

    inv = int(gsum.get("rows_invalid_coord") or 0)
    span = int(gsum.get("rows_internal_span_over_threshold") or 0)
    thr_km = gsum.get("max_internal_distance_km_threshold")

    ir = inv / wc if wc else 0.0
    sr = span / wc if wc else 0.0

    si = _severity_from_ratio(ir, warn_at=iw_warn, error_at=iw_err)
    ss = _severity_from_ratio(sr, warn_at=sp_warn, error_at=sp_err)
    sev = _worst_severity(si, ss)
    if sev is None:
        return []

    return [
        {
            "code": FIELD_GPS_INCONSISTENT,
            "severity": sev,
            "message": (
                f"GPS en muestra: {inv}/{wc} filas con coordenadas inválidas o (0,0); "
                f"{span}/{wc} con puntos válidos separados > {thr_km} km."
            ),
            "idempotency_key": f"{base}:{FIELD_GPS_INCONSISTENT}",
            "explanation": "Heurística sobre columnas lat/lon pareadas en el export; cruces grandes pueden ser legítimos (multi-visita) — validar en terreno.",
            "recommendation": "Revise casos y ajuste `gps_max_internal_distance_km` o ratios en política si el instrumento tiene varios puntos GPS esperados.",
            "evidence": {
                "rows_with_coords": wc,
                "rows_invalid_coord": inv,
                "invalid_ratio": round(ir, 4),
                "rows_internal_span_over_threshold": span,
                "internal_span_ratio": round(sr, 4),
                "max_internal_distance_km_threshold": thr_km,
                "internal_span_km_sample": gsum.get("internal_span_km_sample"),
                "gps_column_pairs": gsum.get("gps_column_pairs"),
            },
        }
    ]


def build_findings_from_response_quality(
    *,
    policy_config: dict[str, Any],
    sync_run_id: int,
    rq: dict[str, Any],
) -> list[FindingDraft]:
    """Compatibilidad: misma lógica que el pipeline tabular solo para respuesta."""
    gate = _tabular_upstream_gate(rq=rq, sync_run_id=sync_run_id)
    if gate:
        return gate
    return _response_quality_row_findings(policy_config, sync_run_id, rq)


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
