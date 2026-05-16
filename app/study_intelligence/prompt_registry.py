"""Central registry for LLM prompts used by study intelligence.

POLICY (obligatory):
- Do NOT scatter prompt strings across services.
- Register every production prompt here with a stable PROMPT_* constant and version.
- Services reference prompt_id + PROMPT_BUNDLE_VERSION only.

Implementation note: template bodies live in version-controlled strings or loaded
artifacts; this module exports identifiers and bundle version for audit trails.
"""

from __future__ import annotations

# Bump when any registered prompt body changes (aligned with AiAssistanceRun.prompt_version).
PROMPT_BUNDLE_VERSION = "0.0.0"

# Future constants, e.g.:
# PROMPT_INSTRUMENT_INSIGHT_SUMMARY_V1 = "instrument_insight_summary_v1"

__all__ = [
    "PROMPT_BUNDLE_VERSION",
]
