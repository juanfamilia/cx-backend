"""Orchestration layer stubs — implement P1+ per 7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md."""

from __future__ import annotations

from app.study_intelligence.contracts import StudyIntelligenceBundle


class StudyIntelligenceService:
    """Orchestrates framework rules, QA heuristics, journey analysis, scoring, insights."""

    __slots__ = ()

    async def build_bundle_for_revision(
        self,
        *,
        revision_id: int,
        company_id: int,
    ) -> StudyIntelligenceBundle:
        """Return composed intelligence for an instrument revision.

        Raises:
            NotImplementedError: until P1 wires QA + journey heuristics server-side.
        """
        raise NotImplementedError(
            "StudyIntelligenceService.build_bundle_for_revision — implement per "
            "docs/7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md phase P1."
        )
