"""Study intelligence — backend motor for journey, QA signals, scoring, insights.

Policy: analytical logic lives here; Angular consumes HTTP/API outputs only.
See docs/7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md
"""

from app.study_intelligence.contracts import (
    ExpectedDropoutZone,
    FatigueRisk,
    InsightCard,
    InsightPriority,
    JourneyPhase,
    MethodologicalSignal,
    OperationalRisk,
    ParticipantJourney,
    SensitivityArea,
    StudyIntelligenceBundle,
)
from app.study_intelligence.layers import StudyIntelligenceService

__all__ = [
    "ExpectedDropoutZone",
    "FatigueRisk",
    "InsightCard",
    "InsightPriority",
    "JourneyPhase",
    "MethodologicalSignal",
    "OperationalRisk",
    "ParticipantJourney",
    "SensitivityArea",
    "StudyIntelligenceBundle",
    "StudyIntelligenceService",
]
