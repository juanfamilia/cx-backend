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


class FailedCustomerEntry(BaseModel):
    """Cliente SurveyToGo para el cual CustomerProjects falló o no se interpretó (catálogo org)."""

    customer_id: str = Field(description="Customer ID en SurveyToGo")
    customer_name: str | None = Field(default=None, description="Nombre devuelto por Customers")
    reason: str = Field(description="Motivo corto (upstream HTTP, parse, etc.)")


class OrganizationStudioProjectsCatalogPage(RemoteFieldCatalogPage):
    """
    Igual que RemoteFieldCatalogPage; `items` son proyectos Studio agregados.
    `failed_customers` lista clientes omitidos sin abortar el resto del barrido.
    """

    failed_customers: list[FailedCustomerEntry] = Field(default_factory=list)
