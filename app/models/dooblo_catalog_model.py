"""Contratos API para catálogo remoto (levantamiento por proveedor; MVP Dooblo)."""

from pydantic import BaseModel, Field


class RemoteFieldCatalogItem(BaseModel):
    """Identificador estable en el sistema remoto + etiqueta para el picker."""

    external_id: str
    title: str
    kind: str = Field(
        default="studio_project",
        description="studio_project | survey | customer | … según proveedor.",
    )


class RemoteFieldCatalogPage(BaseModel):
    provider: str = Field(description='p.ej. "dooblo"')
    items: list[RemoteFieldCatalogItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    query_applied: str | None = None
