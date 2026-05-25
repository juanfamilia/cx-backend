"""Superficie PRE-FIELD: bandas consultivas desde datos persistidos (sin inferencia en Angular)."""

from __future__ import annotations

import math
from typing import Literal

from app.models.field_study_brief_model import (
    FieldBriefConsultHintPublic,
    FieldStudyBriefPublic,
)

BriefDensityBand = Literal["unknown", "thin", "adequate", "rich"]

_THIN_UPPER = 55.0
_ADEQUATE_UPPER = 80.0


def brief_density_band_from_score(score: float | None) -> BriefDensityBand:
    if score is None:
        return "unknown"
    if isinstance(score, float) and math.isnan(score):
        return "unknown"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "unknown"
    if math.isnan(s):
        return "unknown"
    if s < _THIN_UPPER:
        return "thin"
    if s < _ADEQUATE_UPPER:
        return "adequate"
    return "rich"


def enrich_field_study_brief_public(pub: FieldStudyBriefPublic) -> FieldStudyBriefPublic:
    band = brief_density_band_from_score(pub.completeness_score)
    hints: list[FieldBriefConsultHintPublic] = []
    if pub.approval_state == "draft" and band == "thin":
        hints.append(
            FieldBriefConsultHintPublic(
                id="ins-brief-density-thin",
                tone="warn",
                message=(
                    "Según la completitud que figura para este borrador (índice 0–100 guardado en el servidor), "
                    "el contenido todavía es escueto: conviene ampliar un poco el contexto ahora para evitar malentendidos después."
                ),
                apply_label="Ir al brief",
                show_apply=True,
            )
        )
    return pub.model_copy(update={"brief_density_band": band, "consultive_hints": hints})
