"""Tests motor QA_RULE_001–005 (bootstrap PRE-FIELD)."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.instrument_qa_rules_v1 import run_instrument_qa_rules_bootstrap
from app.services.field_instrument_revision_services import DEFAULT_INSTRUMENT_SPEC_STUB

_REPO = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO / "examples" / "instrument_spec_v1.example.json"


def test_example_payload_triggers_all_five_rule_families():
    spec = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    findings = run_instrument_qa_rules_bootstrap(spec)
    rule_ids = {f.rule_id for f in findings}
    assert "QA_RULE_001" in rule_ids
    assert "QA_RULE_002" in rule_ids
    assert "QA_RULE_003" in rule_ids
    assert "QA_RULE_004" in rule_ids
    assert "QA_RULE_005" in rule_ids
    severities = {f.severity for f in findings}
    assert "STOP" in severities
    assert "FIX_NOW" in severities


def test_clean_minimal_spec_has_no_qa_findings():
    spec = {
        "instrument_spec_version": "2026.1-draft",
        "title": "Limpio",
        "blocks": [
            {
                "block_id": "B1",
                "title": "Principal",
                "items": [
                    {
                        "item_id": "Q1",
                        "text": "¿Cómo calificaría el servicio?",
                        "response": {"type": "single", "options": ["Bueno", "Malo"]},
                    }
                ],
            }
        ],
    }
    assert run_instrument_qa_rules_bootstrap(spec) == []


def test_default_creation_stub_has_no_qa_findings():
    assert run_instrument_qa_rules_bootstrap(DEFAULT_INSTRUMENT_SPEC_STUB) == []


def test_cycle_in_branching_stop():
    spec = {
        "instrument_spec_version": "2026.1-draft",
        "title": "Ciclo",
        "blocks": [
            {
                "block_id": "B1",
                "title": "x",
                "items": [
                    {"item_id": "A", "text": "a", "response": {"type": "single", "options": ["1", "2"]}},
                    {"item_id": "B", "text": "b", "response": {"type": "single", "options": ["1", "2"]}},
                ],
            }
        ],
        "branching": {"edges": [{"from": "A", "when": {}, "to": "B"}, {"from": "B", "when": {}, "to": "A"}]},
    }
    findings = run_instrument_qa_rules_bootstrap(spec)
    assert any(f.rule_id == "QA_RULE_005" and "ciclo" in f.message.lower() for f in findings)


def test_quotas_sum_ok_no_rule_003():
    spec = {
        "instrument_spec_version": "2026.1-draft",
        "title": "Cuotas ok",
        "blocks": [
            {
                "block_id": "B1",
                "title": "x",
                "items": [
                    {
                        "item_id": "Q1",
                        "text": "Cuotas",
                        "response": {
                            "type": "quotas",
                            "strata": [
                                {"name": "A", "target_pct": 60},
                                {"name": "B", "target_pct": 40},
                            ],
                        },
                    }
                ],
            }
        ],
    }
    assert not any(f.rule_id == "QA_RULE_003" for f in run_instrument_qa_rules_bootstrap(spec))
