"""Contrato Framework Library: enums alineados al schema y stubs válidos."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.field_framework_template_services import FRAMEWORK_TEMPLATE_STUDY_TYPES
from app.services.instrument_spec_validate import validate_instrument_spec

_REPO = Path(__file__).resolve().parents[1]

# Copia del seed en migración z1y2x3w4v5u6 (stub CX).
STUB_CX_SEED = {
    "instrument_spec_version": "2026.1-draft",
    "study_type": "cx",
    "title": "CX — plantilla base",
    "blocks": [
        {
            "block_id": "SCR",
            "title": "Screening",
            "section_kind": "screener",
            "items": [],
        },
        {
            "block_id": "CX_MAIN",
            "title": "Experiencia y satisfacción",
            "section_kind": "main",
            "items": [],
        },
        {
            "block_id": "DEMO",
            "title": "Demográficos",
            "section_kind": "demographics",
            "items": [],
        },
    ],
}


def test_framework_study_types_match_instrument_spec_schema() -> None:
    schema = json.loads((_REPO / "examples/instrument_spec_v1.schema.json").read_text(encoding="utf-8"))
    enum_vals = frozenset(schema["properties"]["study_type"]["enum"])
    assert FRAMEWORK_TEMPLATE_STUDY_TYPES == enum_vals


def test_seed_stub_cx_validates_against_schema() -> None:
    assert validate_instrument_spec(STUB_CX_SEED) == []
