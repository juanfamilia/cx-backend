"""Ensambla el envelope de memoria compartida para un tenant."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_project_model import FieldProject
from app.models.field_study_model import FieldStudy
from app.models.ins_study_model import InsStudy
from app.platform_intelligence.constants import PLATFORM_MEMORY_SCHEMA_VERSION
from app.platform_intelligence.schemas import (
    CrossFeedChannel,
    DomainLens,
    PlatformMemoryEnvelopePublic,
    ProductFlags,
    SharedPrimitive,
    TenantOperationalFootprint,
)
from app.platform_intelligence.signals_service import list_recent_signals_public


def _static_lenses(flags: ProductFlags) -> list[DomainLens]:
    return [
        DomainLens(
            domain="field",
            title="Siete Field",
            focus=[
                "ejecución",
                "operación",
                "riesgo de campo",
                "calidad operacional",
                "salud",
                "fraude",
                "abandono",
                "cumplimiento metodológico",
            ],
            enabled_for_tenant=flags.field,
        ),
        DomainLens(
            domain="ins",
            title="Siete InS",
            focus=[
                "discurso humano",
                "profundidad cualitativa",
                "patrones emocionales",
                "tensiones",
                "lenguaje",
                "significado",
                "insight discovery",
            ],
            enabled_for_tenant=flags.ins,
        ),
        DomainLens(
            domain="cx",
            title="Siete CX",
            focus=[
                "experiencia observada",
                "customer journey real",
                "interacción humana",
                "auditoría visual",
                "cumplimiento",
                "evidencia multimedia",
            ],
            enabled_for_tenant=flags.cx,
        ),
        DomainLens(
            domain="clever",
            title="Siete Clever",
            focus=[
                "narrativa ejecutiva",
                "storytelling",
                "síntesis",
                "decks",
                "priorización",
                "comunicación para decisión",
            ],
            enabled_for_tenant=flags.clever,
        ),
        DomainLens(
            domain="perfil",
            title="Siete Perfil",
            focus=[
                "segmentación",
                "arquetipos",
                "comportamiento",
                "perfiles",
                "clusters",
                "patrones poblacionales",
            ],
            enabled_for_tenant=flags.perfil,
        ),
    ]


def _static_shared_primitives() -> list[SharedPrimitive]:
    return [
        SharedPrimitive(
            code="findings",
            description="Hallazgos auditables bajo contrato único de plataforma.",
        ),
        SharedPrimitive(
            code="signals",
            description="Señales metodológicas y operativas emitidas por motores de dominio.",
        ),
        SharedPrimitive(
            code="embeddings",
            description="Representaciones vectoriales para similitud y recuperación (roadmap).",
        ),
        SharedPrimitive(
            code="lineage",
            description="Linaje de versiones: instrumento, reglas, aprobaciones, bundles.",
        ),
        SharedPrimitive(
            code="study_intelligence_bundles",
            description="Bundles PRE-FIELD consumibles por FIELD y otros consumidores.",
        ),
        SharedPrimitive(
            code="journey_snapshots",
            description="Recorridos participantes persistidos y enlazados a revisiones.",
        ),
        SharedPrimitive(
            code="transcripts",
            description="Transcripciones y segmentos cualitativos (InS / CX).",
        ),
    ]


def _static_cross_feed() -> list[CrossFeedChannel]:
    """Canales objetivo — la mayoría `planned`; sustituir por `live` cuando existan pipelines."""
    return [
        CrossFeedChannel(
            source="ins",
            sink="field",
            status="planned",
            examples=[
                "frustración / ambigüedad en sesiones → riesgos metodológicos en PRE-FIELD",
                "rechazo a onboarding → expectativas operativas en FIELD",
            ],
        ),
        CrossFeedChannel(
            source="field",
            sink="cx",
            status="planned",
            examples=[
                "anomalías de campo → scoring o alertas de experiencia observada",
            ],
        ),
        CrossFeedChannel(
            source="perfil",
            sink="field",
            status="planned",
            examples=[
                "patrones poblacionales → contextualización de riesgos metodológicos",
            ],
        ),
        CrossFeedChannel(
            source="cx",
            sink="pre_field",
            status="planned",
            examples=[
                "journeys observados → mejoras en diseño de instrumento futuro",
            ],
        ),
        CrossFeedChannel(
            source="ins",
            sink="clever",
            status="planned",
            examples=[
                "insights cualitativos → priorización de narrativa ejecutiva",
            ],
        ),
        CrossFeedChannel(
            source="field",
            sink="clever",
            status="planned",
            examples=[
                "salud operativa → síntesis para decisión",
            ],
        ),
    ]


async def _footprint_for_company(session: AsyncSession, company_id: int) -> TenantOperationalFootprint:
    fp_stmt = select(func.count()).select_from(FieldProject).where(FieldProject.company_id == company_id)
    fs_stmt = select(func.count()).select_from(FieldStudy).where(FieldStudy.company_id == company_id)
    ins_stmt = (
        select(func.count())
        .select_from(InsStudy)
        .where(InsStudy.company_id == company_id)
        .where(InsStudy.deleted_at.is_(None))
    )
    fp = int((await session.execute(fp_stmt)).scalar_one())
    fs = int((await session.execute(fs_stmt)).scalar_one())
    ins = int((await session.execute(ins_stmt)).scalar_one())
    return TenantOperationalFootprint(
        field_project_count=fp,
        field_study_count=fs,
        ins_study_count=ins,
    )


async def build_platform_memory_envelope(
    session: AsyncSession,
    *,
    company_id: int | None,
    flags: ProductFlags,
) -> PlatformMemoryEnvelopePublic:
    footprint = (
        await _footprint_for_company(session, company_id)
        if company_id is not None
        else TenantOperationalFootprint()
    )
    recent_signals = (
        await list_recent_signals_public(session, company_id, limit=15)
        if company_id is not None
        else []
    )
    return PlatformMemoryEnvelopePublic(
        schema_version=PLATFORM_MEMORY_SCHEMA_VERSION,
        company_id=company_id,
        products=flags,
        lenses=_static_lenses(flags),
        shared_primitives=_static_shared_primitives(),
        cross_feed_channels=_static_cross_feed(),
        footprint=footprint,
        recent_signals=recent_signals,
    )
