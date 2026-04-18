"""
Framework catalog (catálogo global de marcos de referencia citables).

Cada Framework representa un modelo reconocido internacionalmente
(SERVQUAL, NPS, CES, Forrester CX Index, ISO 18295, COPC, Kano,
Service Recovery, Moments of Truth, etc.). Cada Framework tiene una o
más FrameworkDimension que son las dimensiones específicas citables
(por ejemplo, SERVQUAL.Empathy, Forrester.Emotion).

Toda cita a un marco se hace por `code` único y la referencia APA
completa vive en `source_citation` para trazabilidad.

Referencia: ver docs/METHODOLOGY.md § 2.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.quality_competency_model import CompetencyFrameworkRef


class FrameworkBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=64)
    name: str = Field(max_length=128)
    authors: Optional[str] = Field(default=None, max_length=512)
    year: Optional[int] = Field(default=None)
    source_citation: Optional[str] = Field(default=None)
    url_reference: Optional[str] = Field(default=None, max_length=512)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)


class Framework(FrameworkBase, table=True):
    __tablename__ = "quality_frameworks"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    dimensions: List["FrameworkDimension"] = Relationship(
        back_populates="framework", sa_relationship_kwargs={"lazy": "noload"}
    )


class FrameworkCreate(SQLModel):
    code: str
    name: str
    authors: Optional[str] = None
    year: Optional[int] = None
    source_citation: Optional[str] = None
    url_reference: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class FrameworkUpdate(SQLModel):
    name: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    source_citation: Optional[str] = None
    url_reference: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FrameworkPublic(FrameworkBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dimensions: Optional[List["FrameworkDimensionPublic"]] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class FrameworksPublic(BaseModel):
    data: List[FrameworkPublic]
    pagination: Pagination


class FrameworkDimensionBase(SQLModel):
    framework_id: int = Field(foreign_key="quality_frameworks.id", index=True)
    code: str = Field(index=True, unique=True, max_length=96)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None)
    order: int = Field(default=0)


class FrameworkDimension(FrameworkDimensionBase, table=True):
    __tablename__ = "quality_framework_dimensions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    framework: Framework = Relationship(
        back_populates="dimensions", sa_relationship_kwargs={"lazy": "noload"}
    )
    competency_refs: List["CompetencyFrameworkRef"] = Relationship(
        back_populates="dimension", sa_relationship_kwargs={"lazy": "noload"}
    )


class FrameworkDimensionCreate(SQLModel):
    framework_id: int
    code: str
    name: str
    description: Optional[str] = None
    order: int = 0


class FrameworkDimensionUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class FrameworkDimensionPublic(FrameworkDimensionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class FrameworkDimensionsPublic(BaseModel):
    data: List[FrameworkDimensionPublic]
    pagination: Pagination


FrameworkPublic.model_rebuild()
