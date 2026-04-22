"""
Industry Template.

Un IndustryTemplate define, para una industria específica, qué competencias
son relevantes, con qué peso sugerido, y cuáles son obligatorias (no
pueden desactivarse por la empresa).

Un par (industry_id, competency_id) es único.

Referencia: ver docs/METHODOLOGY.md § 3.1 y § 4.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Relationship,
    SQLModel,
    UniqueConstraint,
    func,
)

from app.types.pagination import Pagination

# Import en runtime (no solo TYPE_CHECKING): Pydantic/OpenAPI deben resolver
# `competency` en IndustryTemplatePublic; si queda solo forward string, falla
# `class-not-fully-defined` al generar /openapi.json (p. ej. Python 3.13 en Railway).
from app.models.quality_competency_model import QualityCompetencyPublic

if TYPE_CHECKING:
    from app.models.industry_model import Industry
    from app.models.quality_competency_model import QualityCompetency


class IndustryTemplateBase(SQLModel):
    industry_id: int = Field(foreign_key="industries.id", index=True)
    competency_id: int = Field(foreign_key="quality_competencies.id", index=True)
    suggested_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    is_mandatory: bool = Field(default=False)
    notes: Optional[str] = Field(default=None)


class IndustryTemplate(IndustryTemplateBase, table=True):
    __tablename__ = "industry_templates"
    __table_args__ = (
        UniqueConstraint(
            "industry_id", "competency_id", name="uq_industry_templates_industry_comp"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    industry: "Industry" = Relationship(
        back_populates="templates", sa_relationship_kwargs={"lazy": "noload"}
    )
    competency: "QualityCompetency" = Relationship(
        back_populates="industry_templates", sa_relationship_kwargs={"lazy": "noload"}
    )


class IndustryTemplateCreate(SQLModel):
    industry_id: int
    competency_id: int
    suggested_weight: float = 1.0
    is_mandatory: bool = False
    notes: Optional[str] = None


class IndustryTemplateUpdate(SQLModel):
    suggested_weight: Optional[float] = None
    is_mandatory: Optional[bool] = None
    notes: Optional[str] = None


class IndustryTemplatePublic(IndustryTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competency: Optional[QualityCompetencyPublic] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class IndustryTemplatesPublic(BaseModel):
    data: List[IndustryTemplatePublic]
    pagination: Pagination
