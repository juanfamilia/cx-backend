"""Cliente final (sub-tenant B2B2B) bajo una empresa (tenant)."""

from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class EndClientBase(SQLModel):
    name: str = Field(max_length=500)
    external_ref: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class EndClient(EndClientBase, table=True):
    __tablename__ = "end_clients"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)


class EndClientCreate(SQLModel):
    name: str
    external_ref: str | None = None
    notes: str | None = None
    company_id: int | None = None
    """Rol 0: obligatorio si el usuario no tiene empresa asignada."""


class EndClientPublic(EndClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
