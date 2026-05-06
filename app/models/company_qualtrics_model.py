"""Credenciales Qualtrics XM (API v3) por empresa — lectura de campo / catálogo."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class CompanyQualtricsPutBody(SQLModel):
    """Guardar credenciales Qualtrics: origen del datacenter + token (opcional al actualizar token)."""

    base_url: str | None = None
    """Origen HTTPS del tenant, p. ej. ``https://eu.qualtrics.com`` (sin barra final)."""

    api_token: str | None = None


class CompanyQualtricsSettings(SQLModel, table=True):
    __tablename__ = "company_qualtrics_settings"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, unique=True)

    base_url: str = Field(
        max_length=512,
        description="Origen del datacenter Qualtrics (https://*.qualtrics.com).",
    )
    api_token_ciphertext: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Token API (X-API-TOKEN), cifrado en reposo.",
    )

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
