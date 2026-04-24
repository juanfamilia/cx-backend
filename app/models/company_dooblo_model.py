"""Credenciales SurveyToGo/Dooblo almacenadas por empresa (Field)."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


DEFAULT_DOOBLO_BASE_URL = "https://api.dooblo.net/newapi"


class CompanyDoobloPutBody(SQLModel):
    """Cuerpo para guardar credenciales Dooblo por empresa (password opcional al actualizar)."""

    base_url: str | None = None
    api_user: str | None = None
    password: str | None = None


class CompanyDoobloSettings(SQLModel, table=True):
    __tablename__ = "company_dooblo_settings"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, unique=True)

    base_url: str = Field(
        default=DEFAULT_DOOBLO_BASE_URL,
        max_length=512,
        description="Origen de la newapi, sin barra final.",
    )
    api_user: str = Field(
        default="",
        max_length=512,
        description="HTTP Basic: REST_KEY o usuario según documentación Dooblo.",
    )
    # Token Fernet (ASCII) — nunca se expone vía API pública
    password_ciphertext: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
