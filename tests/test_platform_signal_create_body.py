"""Validación de esquemas para platform signals."""

import pytest
from pydantic import ValidationError

from app.platform_intelligence.schemas import PlatformSignalCreateBody


def test_platform_signal_create_rejects_unknown_domain():
    with pytest.raises(ValidationError):
        PlatformSignalCreateBody(
            source_domain="unknown_app",
            signal_code="x",
            summary="y",
        )


def test_platform_signal_create_normalizes_domain_and_code():
    body = PlatformSignalCreateBody(
        source_domain=" INS ",
        signal_code=" qualitative_friction ",
        summary="Ambigüedad recurrente en onboarding",
        severity="medium",
        payload={"session_ids": [1, 2]},
    )
    assert body.source_domain == "ins"
    assert body.signal_code == "qualitative_friction"


def test_platform_signal_accepts_pre_field_domain():
    body = PlatformSignalCreateBody(
        source_domain="pre_field",
        signal_code="test.signal",
        summary="ok",
    )
    assert body.source_domain == "pre_field"
