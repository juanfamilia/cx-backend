"""
Industry model (catálogo global mantenido por superadmin).

Una Industria es una categoría sectorial (Banca, Retail, Salud, Telco, etc.)
que se asigna a cada empresa para precargar un template de competencias
relevantes para ese sector.

Referencia: ver docs/METHODOLOGY.md § 4.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.company_model import Company
    from app.models.industry_template_model import IndustryTemplate


class IndustryBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=64)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None, max_length=64)
    is_active: bool = Field(default=True)


class Industry(IndustryBase, table=True):
    __tablename__ = "industries"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    companies: List["Company"] = Relationship(
        back_populates="industry", sa_relationship_kwargs={"lazy": "noload"}
    )
    templates: List["IndustryTemplate"] = Relationship(
        back_populates="industry", sa_relationship_kwargs={"lazy": "noload"}
    )


class IndustryCreate(SQLModel):
    code: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True


class IndustryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class IndustryPublic(IndustryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class IndustriesPublic(BaseModel):
    data: List[IndustryPublic]
    pagination: Pagination
