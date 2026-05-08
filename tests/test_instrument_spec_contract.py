"""Contrato PRE-FIELD: `instrument_spec` oficial debe validar contra el schema del repo."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.field_instrument_revision_services import DEFAULT_INSTRUMENT_SPEC_STUB
from app.services.instrument_spec_validate import (
    compute_instrument_spec_content_hash,
    validate_instrument_spec,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO_ROOT / "examples" / "instrument_spec_v1.example.json"


def test_official_example_validates_against_schema():
    payload = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    errors = validate_instrument_spec(payload)
    assert errors == [], errors


def test_content_hash_is_stable_for_same_payload():
    payload = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    a = compute_instrument_spec_content_hash(payload)
    b = compute_instrument_spec_content_hash(payload)
    assert a == b and len(a) == 64


def test_default_creation_stub_passes_schema():
    """Plantilla usada al crear revisión sin body debe seguir siendo válida."""
    assert validate_instrument_spec(DEFAULT_INSTRUMENT_SPEC_STUB) == []
