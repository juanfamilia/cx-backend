"""
Gap Analysis Service — IA vs Auditor Humano

Contrasta las respuestas del formulario (verdad humana) con los campos IA
extraídos automáticamente. Genera discrepancias clasificadas por severidad
y un score de confiabilidad del programa por evaluación.

Mapeo de campos:
  1) Si el aspecto tiene `competency_id` y la competencia define `ai_field_hint`
     válido en Evaluation, se usa ese mapeo (prioridad sobre heurística).
  2) Si no, heurística por palabras clave en la descripción (español / inglés).
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.evaluation_model import Evaluation, EvaluationAnswer
from app.models.survey_model import SurveyAspect

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos públicos
# ---------------------------------------------------------------------------

class DiscrepancySeverity(str, Enum):
    CRITICAL = "critical"   # Auditor dice C, IA dice NC con alta confianza
    HIGH     = "high"       # Diferencia importante, confianza media-alta
    MEDIUM   = "medium"     # Diferencia posible, confianza media
    LOW      = "low"        # Discrepancia menor o confianza baja


class GapItem(BaseModel):
    aspect_id: int
    aspect_description: str
    ai_field: str
    auditor_value: Any          # valor registrado por el auditor
    ai_value: Any               # valor extraído por IA
    ai_confidence: float        # 0.0 – 1.0
    discrepancy: bool
    severity: Optional[DiscrepancySeverity]
    note: str


class GapAnalysisResult(BaseModel):
    evaluation_id: int
    total_aspects_mapped: int
    discrepancies_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    reliability_score: float    # 0–100: qué tan alineados están auditor e IA
    items: List[GapItem]


# ---------------------------------------------------------------------------
# Mapa heurístico: palabras clave en descripción → campo IA en Evaluation
# ---------------------------------------------------------------------------
# Cada entrada: (keywords, ai_field, ai_confidence_default)
# Se elige el primer match.

# Campos en Evaluation que aceptamos vía competencia (ai_field_hint); evita typos / RCE por nombre.
_GAP_AI_FIELDS_FROM_COMPETENCY: frozenset[str] = frozenset(
    {
        "greeting_detected",
        "problem_resolved",
        "product_offered",
        "customer_emotion",
        "agent_emotion",
    }
)

_KEYWORD_MAP: List[tuple] = [
    (["saludo", "bienvenida", "greeting", "recib", "acog"], "greeting_detected", 0.85),
    (["identific", "presentación", "presentacion", "quien habla"], "greeting_detected", 0.78),
    (
        ["resolv", "solución", "solucion", "problem", "gestion", "gestión", "contest"],
        "problem_resolved",
        0.80,
    ),
    (["product", "ofert", "venta", "ofrec", "cross", "upsell", "adicional"], "product_offered", 0.75),
    (
        ["emoción", "emocion", "satisf", "trato", "amabilidad", "cortesía", "cortesia", "calidez"],
        "customer_emotion",
        0.70,
    ),
    (["despedida", "cierre", "cerrar", "despid", "agradec"], "greeting_detected", 0.68),
]

# Umbral para considerar discrepancia "activa"
_CONFIDENCE_THRESHOLDS = {
    DiscrepancySeverity.CRITICAL: 0.80,
    DiscrepancySeverity.HIGH:     0.65,
    DiscrepancySeverity.MEDIUM:   0.50,
}


def _match_ai_field(description: str) -> Optional[tuple]:
    """Devuelve (ai_field, confidence) si la descripción del aspecto hace match."""
    desc_lower = description.lower()
    for keywords, ai_field, confidence in _KEYWORD_MAP:
        if any(kw in desc_lower for kw in keywords):
            return ai_field, confidence
    return None


def _mapping_from_competency(aspect: SurveyAspect) -> Optional[tuple[str, float]]:
    """Usa `ai_field_hint` del catálogo de competencias cuando existe y es seguro."""
    comp = getattr(aspect, "competency", None)
    if comp is None:
        return None
    hint = (getattr(comp, "ai_field_hint", None) or "").strip()
    if not hint or hint not in _GAP_AI_FIELDS_FROM_COMPETENCY:
        return None
    return hint, 0.92


def _resolve_ai_mapping(aspect: SurveyAspect) -> Optional[tuple[str, float]]:
    mapped = _mapping_from_competency(aspect)
    if mapped:
        return mapped
    return _match_ai_field(aspect.description or "")


def _normalize_auditor(answer: EvaluationAnswer) -> Optional[bool]:
    """Convierte respuesta humana a bool para comparar con IA."""
    if answer.value_boolean is not None:
        return answer.value_boolean
    if answer.value_number is not None:
        # Número > 0 o >= mitad del máximo se considera cumplido
        return answer.value_number > 0
    return None


def _normalize_ai(evaluation: Evaluation, ai_field: str) -> Optional[bool]:
    """Extrae campo IA como bool. Para campos numéricos usa umbral 50."""
    val = getattr(evaluation, ai_field, None)
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        pos = {
            "satisfecho",
            "contento",
            "feliz",
            "positivo",
            "amable",
            "profesional",
            "neutral",
            "tranquilo",
            "agradecido",
            "conforme",
        }
        neg = {
            "frustrado",
            "molesto",
            "enojado",
            "negativo",
            "apático",
            "apatico",
            "irritado",
            "enfadado",
            "hostil",
            "insatisfecho",
        }
        lower = val.lower()
        if lower in pos:
            return True
        if lower in neg:
            return False
        return None
    if isinstance(val, (int, float)):
        # NPS inferido 0–10: mitad de escala como umbral neutro
        if ai_field == "nps_inferred":
            return val >= 7
        return val >= 50
    return None


def _classify_severity(
    auditor_val: Optional[bool],
    ai_val: Optional[bool],
    confidence: float,
) -> Optional[DiscrepancySeverity]:
    if auditor_val is None or ai_val is None:
        return None
    if auditor_val == ai_val:
        return None
    # Auditor dice cumplido, IA dice no cumplido → más grave
    if auditor_val is True and ai_val is False:
        if confidence >= _CONFIDENCE_THRESHOLDS[DiscrepancySeverity.CRITICAL]:
            return DiscrepancySeverity.CRITICAL
        if confidence >= _CONFIDENCE_THRESHOLDS[DiscrepancySeverity.HIGH]:
            return DiscrepancySeverity.HIGH
        return DiscrepancySeverity.MEDIUM
    # Auditor dice no cumplido, IA dice cumplido → menos grave (podría ser falso positivo de IA)
    if confidence >= _CONFIDENCE_THRESHOLDS[DiscrepancySeverity.HIGH]:
        return DiscrepancySeverity.HIGH
    return DiscrepancySeverity.MEDIUM


# ---------------------------------------------------------------------------
# Servicio principal
# ---------------------------------------------------------------------------

async def compute_gap_analysis(
    session: AsyncSession,
    evaluation_id: int,
) -> GapAnalysisResult:
    """
    Calcula el Gap Analysis para una evaluación concreta.
    """
    # Cargar evaluación con respuestas y aspectos
    q = (
        select(Evaluation)
        .where(Evaluation.id == evaluation_id, Evaluation.deleted_at.is_(None))
        .options(
            selectinload(Evaluation.evaluation_answers).selectinload(
                EvaluationAnswer.aspect
            ).selectinload(SurveyAspect.competency)
        )
    )
    result = await session.execute(q)
    evaluation = result.scalars().first()

    if not evaluation:
        from app.utils.exeptions import NotFoundException
        raise NotFoundException("Evaluation not found")

    items: List[GapItem] = []
    mapped = 0

    for answer in (evaluation.evaluation_answers or []):
        if answer.deleted_at is not None:
            continue
        aspect: SurveyAspect = answer.aspect
        if not aspect:
            continue

        match = _resolve_ai_mapping(aspect)
        if not match:
            continue

        ai_field, base_confidence = match
        mapped += 1

        auditor_bool = _normalize_auditor(answer)
        ai_bool = _normalize_ai(evaluation, ai_field)

        discrepancy = (
            auditor_bool is not None
            and ai_bool is not None
            and auditor_bool != ai_bool
        )
        severity = _classify_severity(auditor_bool, ai_bool, base_confidence) if discrepancy else None

        note = ""
        if auditor_bool is None:
            note = "Auditor no respondió este ítem"
        elif ai_bool is None:
            note = "IA no procesó este campo (análisis pendiente)"
        elif discrepancy:
            direction = (
                "Auditor marcó cumplido, IA detectó incumplimiento"
                if auditor_bool and not ai_bool
                else "Auditor marcó incumplimiento, IA detectó cumplimiento"
            )
            note = f"{direction} (confianza IA: {base_confidence:.0%})"

        items.append(
            GapItem(
                aspect_id=aspect.id,
                aspect_description=aspect.description,
                ai_field=ai_field,
                auditor_value=answer.value_boolean if answer.value_boolean is not None else answer.value_number,
                ai_value=getattr(evaluation, ai_field, None),
                ai_confidence=base_confidence,
                discrepancy=discrepancy,
                severity=severity,
                note=note,
            )
        )

    discrepancies = [i for i in items if i.discrepancy]
    critical = sum(1 for i in discrepancies if i.severity == DiscrepancySeverity.CRITICAL)
    high     = sum(1 for i in discrepancies if i.severity == DiscrepancySeverity.HIGH)
    medium   = sum(1 for i in discrepancies if i.severity == DiscrepancySeverity.MEDIUM)
    low      = sum(1 for i in discrepancies if i.severity == DiscrepancySeverity.LOW)

    # Reliability: % de aspectos mapeados sin discrepancia
    reliability = (
        round((mapped - len(discrepancies)) / mapped * 100, 1) if mapped > 0 else 100.0
    )

    return GapAnalysisResult(
        evaluation_id=evaluation_id,
        total_aspects_mapped=mapped,
        discrepancies_found=len(discrepancies),
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
        reliability_score=reliability,
        items=items,
    )


async def get_gap_summary_for_campaign(
    session: AsyncSession,
    campaign_id: int,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Agrega resultados de Gap Analysis para todas las evaluaciones de una campaña.
    Devuelve promedios y ranking de discrepancias más frecuentes.
    """
    from sqlalchemy import func as sqlfunc
    from app.models.campaign_model import Campaign

    q = select(Evaluation).where(
        Evaluation.campaigns_id == campaign_id,
        Evaluation.deleted_at.is_(None),
    )
    if company_id:
        q = q.join(Campaign, Evaluation.campaigns_id == Campaign.id).where(
            Campaign.company_id == company_id
        )

    rows = (await session.execute(q)).scalars().all()

    all_results = []
    for ev in rows:
        try:
            gap = await compute_gap_analysis(session, ev.id)
            all_results.append(gap)
        except Exception as exc:
            logger.warning("gap_summary skip evaluation_id=%s: %s", ev.id, exc)

    if not all_results:
        return {
            "campaign_id": campaign_id,
            "evaluations_analyzed": 0,
            "avg_reliability_score": None,
            "total_critical": 0,
            "field_discrepancy_ranking": [],
        }

    avg_reliability = round(
        sum(r.reliability_score for r in all_results) / len(all_results), 1
    )
    total_critical = sum(r.critical_count for r in all_results)

    # Ranking de campos con más discrepancias
    field_counts: Dict[str, int] = {}
    for r in all_results:
        for item in r.items:
            if item.discrepancy:
                field_counts[item.ai_field] = field_counts.get(item.ai_field, 0) + 1

    ranking = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "campaign_id": campaign_id,
        "evaluations_analyzed": len(all_results),
        "avg_reliability_score": avg_reliability,
        "total_critical": total_critical,
        "field_discrepancy_ranking": [
            {"field": f, "count": c} for f, c in ranking
        ],
    }
