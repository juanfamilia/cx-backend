"""Esquemas HTTP para la capa de inteligencia compartida (un cerebro, varias vistas)."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
        description="field | ins | cx | clever | perfil",
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


class PlatformMemoryEnvelopePublic(BaseModel):
    """Envelope único: cómo piensa la plataforma como sistema, no como silos."""

    schema_version: str = Field(description="Versión del JSON público.")
    company_id: int | None = Field(description="Tenant resuelto o null si no aplica.")
    products: ProductFlags
    lenses: list[DomainLens]
    shared_primitives: list[SharedPrimitive]
    cross_feed_channels: list[CrossFeedChannel]
    footprint: TenantOperationalFootprint
