"""Inteligencia de plataforma — cerebro compartido (contratos HTTP y ensamblaje por tenant)."""

from app.platform_intelligence.constants import PLATFORM_MEMORY_SCHEMA_VERSION
from app.platform_intelligence.schemas import PlatformMemoryEnvelopePublic
from app.platform_intelligence.service import build_platform_memory_envelope

__all__ = [
    "PLATFORM_MEMORY_SCHEMA_VERSION",
    "PlatformMemoryEnvelopePublic",
    "build_platform_memory_envelope",
]
