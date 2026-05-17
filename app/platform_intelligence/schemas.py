"""Esquemas HTTP para la capa de inteligencia compartida (un cerebro, varias vistas)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ProductFlags(BaseModel):
    """Espejo de capacidades por tenant (alineado a entitlements)."""

    cx: bool = Field(description="CX — experiencia observada (producto base).")
    ins: bool = Field(description="InS — profundidad cualitativa / discurso.")
    field: bool = Field(description="Field — ejecución y operación de campo.")
    clever: bool = Field(description="Clever — narrativa ejecutiva gobernada.")
    perfil: bool = Field(
        default=False,
        description="Perfil — segmentación / arquetipos (roadmap; sin flag en companies aún).",
    )


class DomainLens(BaseModel):
    """Vista especializada sobre la misma memoria de plataforma."""

    domain: str = Field(
        ...,
        description="field | pre_field | ins | cx | clever | perfil",
        examples=["field"],
    )
    title: str
    focus: list[str] = Field(
        default_factory=list,
        description="Qué tipo de inteligencia cubre esta vista.",
    )
    enabled_for_tenant: bool = Field(
        description="Si el tenant actual tiene el producto activo (Perfil hasta roadmap puede ser false).",
    )


class SharedPrimitive(BaseModel):
    """Primitiva que debe converger en el cerebro compartido (contrato evolutivo)."""

    code: str = Field(
        ...,
        examples=["findings"],
        description="Identificador estable para clientes y pipelines.",
    )
    description: str


class CrossFeedChannel(BaseModel):
    """Canal orientativo InS→Field→CX… — `status` indica madurez de integración."""

    source: str = Field(..., description="Dominio origen (field, ins, cx, clever, perfil).")
    sink: str = Field(..., description="Dominio destino.")
    status: str = Field(
        ...,
        description="planned | partial | live — según implemented pipelines.",
    )
    examples: list[str] = Field(
        default_factory=list,
        description="Ejemplos de señales o artefactos que deben cruzar.",
    )


class TenantOperationalFootprint(BaseModel):
    """Conteos mínimos por tenant (profundizar con vector store / embeddings después)."""

    field_study_count: int = 0
    field_project_count: int = 0
    ins_study_count: int = 0


_ALLOWED_DOMAINS = frozenset({"field", "pre_field", "ins", "cx", "clever", "perfil", "platform"})


class PlatformSignalCreateBody(BaseModel):
    """Cuerpo para registrar una señal en la memoria compartida del tenant."""

    source_domain: str = Field(max_length=32)
    signal_code: str = Field(max_length=64)
    summary: str = Field(max_length=4000)
    severity: str | None = Field(default=None, max_length=16)
    payload: dict = Field(default_factory=dict)
    field_study_id: int | None = None
    field_project_id: int | None = None
    ins_study_id: int | None = None

    @field_validator("source_domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in _ALLOWED_DOMAINS:
            raise ValueError(
                f"source_domain debe ser uno de: {', '.join(sorted(_ALLOWED_DOMAINS))}",
            )
        return s

    @field_validator("signal_code")
    @classmethod
    def strip_code(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("signal_code no puede estar vacío")
        return s


class PlatformSignalPublic(BaseModel):
    """Evento de señal ya persistido."""

    id: int
    company_id: int
    source_domain: str
    signal_code: str
    severity: str | None
    summary: str
    payload: dict
    field_study_id: int | None
    field_project_id: int | None
    ins_study_id: int | None
    created_by_user_id: int | None
    created_at: str


class PlatformMemoryEnvelopePublic(BaseModel):
    """Envelope único: cómo piensa la plataforma como sistema, no como silos."""

    schema_version: str = Field(description="Versión del JSON público.")
    company_id: int | None = Field(description="Tenant resuelto o null si no aplica.")
    products: ProductFlags
    lenses: list[DomainLens]
    shared_primitives: list[SharedPrimitive]
    cross_feed_channels: list[CrossFeedChannel]
    footprint: TenantOperationalFootprint
    recent_signals: list[PlatformSignalPublic] = Field(
        default_factory=list,
        description="Últimas señales cross-dominio persistidas para el tenant.",
    )
