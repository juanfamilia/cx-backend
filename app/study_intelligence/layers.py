"""Orchestration layer — Study Intelligence P1 (QA + journey + Readiness)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.study_intelligence.pipeline import build_study_intelligence_bundle_for_revision
from app.study_intelligence.schemas import StudyIntelligenceBundlePublic


class StudyIntelligenceService:
    """Orquesta framework rules, QA heuristics, journey analysis, scoring, insights."""

    __slots__ = ()

    async def build_bundle_for_revision(
        self,
        session: AsyncSession,
        user: User,
        *,
        revision_id: int,
        company_id: int | None,
    ) -> StudyIntelligenceBundlePublic:
        """Devuelve bundle de inteligencia para una revisión (sin persistir corrida QA nueva)."""
        return await build_study_intelligence_bundle_for_revision(
            session, user, revision_id, company_id
        )
