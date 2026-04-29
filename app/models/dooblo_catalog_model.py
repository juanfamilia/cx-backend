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
    studio_customer_id: str | None = Field(
        default=None,
        description="Si el ítem viene de agregación org-wide (SurveyToGo Customers × CustomerProjects).",
    )
    studio_customer_name: str | None = Field(
        default=None,
        description="Nombre del cliente SurveyToGo cuando aplica.",
    )


class RemoteFieldCatalogPage(BaseModel):
    provider: str = Field(description='p.ej. "dooblo"')
    items: list[RemoteFieldCatalogItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    query_applied: str | None = None
