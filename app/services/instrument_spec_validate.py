"""Validación de `instrument_spec` contra JSON Schema (PRE-FIELD / Auto QA v1).

Ver docs/7FIELD_STRUCTURAL_DECISIONS_V1.md (L2) y docs/7FIELD_PRE_FIELD_INTELLIGENCE_V1.md.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _REPO_ROOT / "examples" / "instrument_spec_v1.schema.json"


class InstrumentSpecSchemaError(RuntimeError):
    """No se pudo cargar el schema desde disco (instalación o checkout incompleto)."""


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    if not _SCHEMA_PATH.is_file():
        raise InstrumentSpecSchemaError(f"Missing schema file: {_SCHEMA_PATH}")
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_instrument_spec(instance: dict[str, Any]) -> list[str]:
    """Devuelve lista de mensajes de error (vacía si el payload cumple el schema)."""
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for err in validator.iter_errors(instance):
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"{path}: {err.message}")
    errors.sort()
    return errors


def canonical_instrument_spec_bytes(spec: dict[str, Any]) -> bytes:
    """Serialización estable para hashing y auditoría (orden de claves fijo)."""
    return json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def compute_instrument_spec_content_hash(spec: dict[str, Any]) -> str:
    """SHA-256 hex del JSON canónico (sirve para `content_hash` y trazabilidad)."""
    return hashlib.sha256(canonical_instrument_spec_bytes(spec)).hexdigest()
