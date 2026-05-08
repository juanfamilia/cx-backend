"""Contrato PRE-FIELD: `instrument_spec` oficial debe validar contra el schema del repo."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.instrument_spec_validate import validate_instrument_spec

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO_ROOT / "examples" / "instrument_spec_v1.example.json"


def test_official_example_validates_against_schema():
    payload = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    errors = validate_instrument_spec(payload)
    assert errors == [], errors
