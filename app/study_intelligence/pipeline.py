"""Ensambla `StudyIntelligenceBundlePublic` desde revision + brief + QA + Readiness."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_instrument_revision_model import FieldInstrumentRevisionPublic
from app.models.user_model import User
from app.services.field_instrument_revision_services import get_instrument_revision
from app.services.field_readiness_services import get_readiness_for_revision
from app.services.field_study_brief_services import get_field_study_brief_public
from app.services.instrument_qa_rules_v1 import (
    QA_RULESET_BOOTSTRAP_V1,
    InstrumentQAFinding,
    _iter_blocks_items,
    run_instrument_qa_rules_bootstrap,
    summarize_qa_severities,
)

from app.study_intelligence.constants import STUDY_INTELLIGENCE_ENGINE_VERSION
from app.study_intelligence.contracts import (
    ExpectedDropoutZone,
    FatigueRisk,
    InsightCard,
    InsightPriority,
    MethodologicalSignal,
    OperationalRisk,
    ParticipantJourney,
    SensitivityArea,
    StudyIntelligenceBundle,
)
from app.study_intelligence.journey_heuristics import (
    build_journey_phases,
    extract_guided_strings,
    trim_join_brief,
)
from app.study_intelligence.schemas import (
    ExpectedDropoutZonePublic,
    FatigueRiskPublic,
    InsightCardPublic,
    JourneyPhasePublic,
    MethodologicalSignalPublic,
    OperationalRiskPublic,
    ParticipantJourneyPublic,
    SensitivityAreaPublic,
    StudyIntelligenceBundlePublic,
)
from app.study_intelligence.persistence import upsert_participant_journey_snapshot

logger = logging.getLogger(__name__)

READINESS_BLOCK_HUMAN: dict[str, str] = {
    "revision_archived": "La revisión está archivada; no aplica salida a campo.",
    "brief_not_approved": "El brief del estudio no está aprobado según la política Readiness.",
    "signatory_grants_not_loaded": "No se pudo validar la matriz de signatarios autorizados.",
    "schema_validation_missing": "Falta ejecutar validación de esquema JSON sobre este instrumento.",
    "schema_validation_failed": "La última validación de esquema del instrumento falló.",
    "schema_validation_stale": "La validación guardada no corresponde al contenido actual del spec.",
    "qa_run_missing": "No hay una corrida de Auto QA registrada para esta revisión.",
    "qa_stop_present": "Hay hallazgos Auto QA con severidad STOP.",
    "qa_fix_now_present": "Hay hallazgos Auto QA FIX_NOW que bloquean según política.",
}


def _readiness_message(code: str) -> str:
    if code.startswith("no_signatories_for_"):
        role = code.replace("no_signatories_for_", "")
        return f"No hay signatarios configurados para el rol {role}."
    return READINESS_BLOCK_HUMAN.get(code, f"Bloqueo Readiness: {code}")


def _count_items(spec: dict[str, Any]) -> int:
    return sum(1 for _, _ in _iter_blocks_items(spec))


def assemble_study_intelligence_bundle(
    *,
    revision_pub: FieldInstrumentRevisionPublic,
    spec: dict[str, Any],
    brief_payload: dict[str, Any],
    qa_findings: list[InstrumentQAFinding],
    readiness_blocking_codes: tuple[str, ...],
) -> StudyIntelligenceBundle:
    guided = extract_guided_strings(brief_payload if isinstance(brief_payload, dict) else {})
    brief_blob = trim_join_brief(brief_payload if isinstance(brief_payload, dict) else {}, guided)

    phases_tuple, flags = build_journey_phases(spec, brief_blob)
    counts: list[int] = flags["counts"]

    pj = ParticipantJourney(
        study_id=revision_pub.study_id,
        instrument_revision_id=revision_pub.id,
        brief_snapshot_hash=(revision_pub.brief_snapshot_hash or None) or None,
        instrument_spec_content_hash=revision_pub.content_hash or None,
        framework_catalog_version=revision_pub.framework_catalog_version,
        phases=phases_tuple,
    )

    stops, fix_now, monitor = summarize_qa_severities(qa_findings)

    methodological_signals: list[MethodologicalSignal] = []
    trace_rules_stop: list[str] = []
    trace_rules_fix: list[str] = []
    trace_rules_mon: list[str] = []
    for f in qa_findings:
        methodological_signals.append(
            MethodologicalSignal(
                code=f.rule_id,
                message_human=f.message,
                severity=f.severity,
                linked_block_id=f.block_id,
                framework_rule_ref=f.rule_id,
            )
        )
        if f.severity == "STOP":
            trace_rules_stop.append(f.rule_id)
        elif f.severity == "FIX_NOW":
            trace_rules_fix.append(f.rule_id)
        elif f.severity == "MONITOR":
            trace_rules_mon.append(f.rule_id)

    operational_risks: list[OperationalRisk] = []
    for code in readiness_blocking_codes:
        operational_risks.append(
            OperationalRisk(
                code=f"readiness_{code}",
                message_human=_readiness_message(code),
                severity="high",
                source_rule_id=code,
            )
        )

    if stops > 0:
        operational_risks.append(
            OperationalRisk(
                code="qa_stop_instant_pass",
                message_human=(
                    f"Pasada heurística actual: {stops} hallazgo(s) STOP; conviene resolverlos antes de ejecutar."
                ),
                severity="high",
                source_rule_id="QA_RULESET_BOOTSTRAP_V1",
            )
        )

    fatigue_risks: list[FatigueRisk] = []
    total_blocks = int(flags["total_blocks"])
    if flags["heavy_survey"]:
        fatigue_risks.append(
            FatigueRisk(
                code="BLOCK_COUNT_HIGH",
                message_human=(
                    "Muchos bloques: si el tiempo del respondente es corto, priorizar lo que mueve decisión."
                ),
                level="high",
            )
        )
    elif total_blocks >= 6:
        fatigue_risks.append(
            FatigueRisk(
                code="BLOCK_COUNT_MODERATE",
                message_human="Longitud moderada: vigilar ritmo en selección y experiencia central.",
                level="medium",
            )
        )

    if flags["exp_heavy"] and flags["has_instrument"]:
        exp_first_block = phases_tuple[2].block_ids[0] if phases_tuple[2].block_ids else None
        fatigue_risks.append(
            FatigueRisk(
                code="EXPERIENCE_SEGMENT_HEAVY",
                message_human=(
                    "La sección de experiencia central concentra varios bloques; riesgo de fatiga si las preguntas son densas."
                ),
                level="high" if total_blocks >= 8 else "medium",
                linked_block_id=exp_first_block,
            )
        )

    sensitivity_areas: list[SensitivityArea] = []
    if flags["sensitive_hint"]:
        sensitivity_areas.append(
            SensitivityArea(
                code="BRIEF_TOPIC_HINT",
                label_human="Sensibilidad inferida del brief",
                rationale_human=str(flags["sensitive_hint"]),
                linked_block_ids=(),
            )
        )

    dropout_zones: list[ExpectedDropoutZone] = []
    if counts[1] > 0 and flags["has_instrument"]:
        dropout_zones.append(
            ExpectedDropoutZone(
                phase_key="screening",
                linked_block_id=phases_tuple[1].block_ids[0]
                if phases_tuple[1].block_ids
                else None,
                message_human=(
                    "La selección suele concentrar abandono si es larga o confusa; revisar claridad y filtros."
                ),
                confidence="heuristic",
            )
        )

    insight_cards: list[InsightCard] = []

    if flags["has_instrument"] and flags["heavy_survey"]:
        insight_cards.append(
            InsightCard(
                insight_id="global_block_count",
                headline="Instrumento largo",
                body=(
                    "Hay muchos bloques: si el tiempo con quien responde es corto, conviene "
                    "priorizar lo que mueve decisión."
                ),
                priority=InsightPriority.MEDIUM,
                tone="observe",
                trace_heuristic_ids=("HEUR_BLOCK_COUNT_9",),
            )
        )

    if flags["has_instrument"] and flags["demo_early"]:
        insight_cards.append(
            InsightCard(
                insight_id="global_demo_early",
                headline="Perfil temprano en el flujo",
                body=(
                    "El perfil aparece muy arriba en el flujo; muchas veces funciona mejor después "
                    "de la experiencia central."
                ),
                priority=InsightPriority.MEDIUM,
                tone="observe",
                trace_heuristic_ids=("HEUR_DEMO_EARLY",),
            )
        )

    if flags["has_instrument"] and flags["induced_early"]:
        insight_cards.append(
            InsightCard(
                insight_id="global_positive_early",
                headline="Valoración antes del relato",
                body=(
                    "Hay valoraciones muy positivas antes del relato de experiencia; puede sesgar "
                    "lo que viene después."
                ),
                priority=InsightPriority.HIGH,
                tone="caution",
                trace_heuristic_ids=("HEUR_POSITIVE_LEAN_EARLY",),
            )
        )

    if flags["sensitive_hint"]:
        insight_cards.append(
            InsightCard(
                insight_id="global_sensitive_topic",
                headline="Posible tema sensible",
                body=str(flags["sensitive_hint"]),
                priority=InsightPriority.MEDIUM,
                tone="observe",
                trace_heuristic_ids=("HEUR_SENSITIVE_TOPIC",),
            )
        )

    if "fricc" in brief_blob and flags["has_instrument"] and counts[2] > 0:
        insight_cards.append(
            InsightCard(
                insight_id="brief_friction_alignment",
                headline="Alineación brief ↔ experiencia",
                body=(
                    "Si el brief habla de fricción, conviene que ese foco se refleje en las preguntas "
                    "del tramo central."
                ),
                priority=InsightPriority.MEDIUM,
                tone="observe",
                trace_heuristic_ids=("HEUR_BRIEF_FRICTION",),
            )
        )

    if stops > 0:
        insight_cards.append(
            InsightCard(
                insight_id="qa_aggregate_stop",
                headline="Auto QA: hallazgos críticos (STOP)",
                body=(
                    f"El motor detectó {stops} hallazgo(s) STOP. Revise routing, escalas y redacción "
                    "antes de comprometer campo."
                ),
                priority=InsightPriority.MUST_ACT,
                tone="caution",
                trace_rule_ids=tuple(sorted(set(trace_rules_stop))),
            )
        )
    elif fix_now > 0:
        insight_cards.append(
            InsightCard(
                insight_id="qa_aggregate_fix_now",
                headline="Auto QA: mejoras recomendadas (FIX_NOW)",
                body=(
                    f"Hay {fix_now} recomendación(es) FIX_NOW: conviene una pasada humana antes de ejecutar."
                ),
                priority=InsightPriority.HIGH,
                tone="caution",
                trace_rule_ids=tuple(sorted(set(trace_rules_fix))),
            )
        )
    elif monitor > 0 and flags["has_instrument"]:
        insight_cards.append(
            InsightCard(
                insight_id="qa_aggregate_monitor",
                headline="Auto QA: puntos a vigilar",
                body=(
                    f"Hay {monitor} observación(es) MONITOR; el borrador no muestra problemas graves automáticos."
                ),
                priority=InsightPriority.FYI,
                tone="bright",
                trace_rule_ids=tuple(sorted(set(trace_rules_mon))),
            )
        )
    elif flags["has_instrument"] and stops == 0 and fix_now == 0:
        insight_cards.append(
            InsightCard(
                insight_id="qa_clean_heuristic",
                headline="Auto QA (instantáneo)",
                body="La pasada heurística actual no encontró STOP ni FIX_NOW en este spec.",
                priority=InsightPriority.FYI,
                tone="bright",
                trace_rule_ids=(),
            )
        )

    if readiness_blocking_codes:
        first = readiness_blocking_codes[0]
        insight_cards.append(
            InsightCard(
                insight_id=f"readiness_{first}",
                headline="Readiness pendiente",
                body=_readiness_message(first),
                priority=InsightPriority.MUST_ACT,
                tone="caution",
                trace_heuristic_ids=(f"READINESS:{first}",),
            )
        )

    contextual_scores: dict[str, Any] = {
        "block_count": total_blocks,
        "item_count": _count_items(spec),
        "qa_stop_count": stops,
        "qa_fix_now_count": fix_now,
        "qa_monitor_count": monitor,
        "fatigue_overall": (
            "high"
            if flags["heavy_survey"]
            else ("medium" if total_blocks >= 6 else ("low" if flags["has_instrument"] else "unknown"))
        ),
        "emotional_load_hint": "elevated" if flags["sensitive_hint"] else "typical",
    }

    return StudyIntelligenceBundle(
        participant_journey=pj,
        operational_risks=tuple(operational_risks),
        methodological_signals=tuple(methodological_signals),
        fatigue_risks=tuple(fatigue_risks),
        sensitivity_areas=tuple(sensitivity_areas),
        expected_dropout_zones=tuple(dropout_zones),
        insight_cards=tuple(insight_cards),
        contextual_scores=contextual_scores,
        ruleset_versions=(QA_RULESET_BOOTSTRAP_V1, STUDY_INTELLIGENCE_ENGINE_VERSION),
    )


def bundle_to_public(
    contract: StudyIntelligenceBundle,
    *,
    participant_journey_snapshot_id: int | None = None,
) -> StudyIntelligenceBundlePublic:
    pj = contract.participant_journey
    pj_pub = None
    if pj is not None:
        pj_pub = ParticipantJourneyPublic(
            study_id=pj.study_id,
            instrument_revision_id=pj.instrument_revision_id,
            brief_snapshot_hash=pj.brief_snapshot_hash,
            instrument_spec_content_hash=pj.instrument_spec_content_hash,
            framework_catalog_version=pj.framework_catalog_version,
            phases=[
                JourneyPhasePublic(
                    phase_key=p.phase_key,
                    order_index=p.order_index,
                    title=p.title,
                    narrative_summary=p.narrative_summary,
                    block_ids=list(p.block_ids),
                )
                for p in pj.phases
            ],
        )

    return StudyIntelligenceBundlePublic(
        engine_version=STUDY_INTELLIGENCE_ENGINE_VERSION,
        ruleset_versions=list(contract.ruleset_versions),
        participant_journey_snapshot_id=participant_journey_snapshot_id,
        participant_journey=pj_pub,
        operational_risks=[
            OperationalRiskPublic(
                code=r.code,
                message_human=r.message_human,
                severity=r.severity,
                linked_block_id=r.linked_block_id,
                linked_item_id=r.linked_item_id,
                source_rule_id=r.source_rule_id,
            )
            for r in contract.operational_risks
        ],
        methodological_signals=[
            MethodologicalSignalPublic(
                code=m.code,
                message_human=m.message_human,
                severity=m.severity,
                linked_block_id=m.linked_block_id,
                framework_rule_ref=m.framework_rule_ref,
            )
            for m in contract.methodological_signals
        ],
        fatigue_risks=[
            FatigueRiskPublic(
                code=f.code,
                message_human=f.message_human,
                level=f.level,
                linked_block_id=f.linked_block_id,
            )
            for f in contract.fatigue_risks
        ],
        sensitivity_areas=[
            SensitivityAreaPublic(
                code=s.code,
                label_human=s.label_human,
                rationale_human=s.rationale_human,
                linked_block_ids=list(s.linked_block_ids),
            )
            for s in contract.sensitivity_areas
        ],
        expected_dropout_zones=[
            ExpectedDropoutZonePublic(
                phase_key=z.phase_key,
                linked_block_id=z.linked_block_id,
                message_human=z.message_human,
                confidence=z.confidence,
            )
            for z in contract.expected_dropout_zones
        ],
        insight_cards=[
            InsightCardPublic(
                insight_id=i.insight_id,
                headline=i.headline,
                body=i.body,
                priority=i.priority,
                tone=i.tone,
                trace_rule_ids=list(i.trace_rule_ids),
                trace_heuristic_ids=list(i.trace_heuristic_ids),
            )
            for i in contract.insight_cards
        ],
        contextual_scores=dict(contract.contextual_scores),
    )


async def build_study_intelligence_bundle_for_revision(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: int | None,
) -> StudyIntelligenceBundlePublic:
    pub, spec = await get_instrument_revision(
        session, user, revision_id, company_id, include_spec=True
    )
    if spec is None:
        spec = {}

    brief_row = await get_field_study_brief_public(session, user, pub.study_id, company_id)

    readiness = await get_readiness_for_revision(session, user, revision_id, company_id)

    qa_findings = run_instrument_qa_rules_bootstrap(spec)

    bundle = assemble_study_intelligence_bundle(
        revision_pub=pub,
        spec=spec,
        brief_payload=dict(brief_row.payload_json),
        qa_findings=qa_findings,
        readiness_blocking_codes=tuple(readiness.blocking_codes),
    )
    snapshot_id: int | None = None
    try:
        snapshot_id = await upsert_participant_journey_snapshot(
            session, revision_pub=pub, bundle=bundle
        )
    except Exception:
        logger.exception("study_intelligence: falló persistencia participant_journey snapshot")
    return bundle_to_public(bundle, participant_journey_snapshot_id=snapshot_id)
