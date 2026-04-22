"""
Company Competency Config.

Override a nivel de empresa sobre el template de industria. Permite:
  - Activar/desactivar una competencia del template (respetando
    is_mandatory del IndustryTemplate).
  - Ajustar el peso propio de la competencia para esa empresa.
  - Registrar notas de justificación.

Un par (company_id, competency_id) es único.

Referencia: ver docs/METHODOLOGY.md § 3.1.
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

# Runtime: Pydantic debe resolver `competency` para OpenAPI (/openapi.json).
from app.models.quality_competency_model import QualityCompetencyPublic

if TYPE_CHECKING:
    from app.models.quality_competency_model import QualityCompetency


class CompanyCompetencyConfigBase(SQLModel):
    company_id: int = Field(foreign_key="companies.id", index=True)
    competency_id: int = Field(foreign_key="quality_competencies.id", index=True)
    is_enabled: bool = Field(default=True)
    custom_weight: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    custom_notes: Optional[str] = Field(default=None)
    created_by_user_id: Optional[int] = Field(
        default=None, foreign_key="users.id", index=True
    )


class CompanyCompetencyConfig(CompanyCompetencyConfigBase, table=True):
    __tablename__ = "company_competency_configs"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "competency_id", name="uq_company_comp_config_company_comp"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    competency: "QualityCompetency" = Relationship(
        back_populates="company_configs", sa_relationship_kwargs={"lazy": "noload"}
    )


class CompanyCompetencyConfigCreate(SQLModel):
    company_id: int
    competency_id: int
    is_enabled: bool = True
    custom_weight: Optional[float] = None
    custom_notes: Optional[str] = None
    created_by_user_id: Optional[int] = None


class CompanyCompetencyConfigUpdate(SQLModel):
    is_enabled: Optional[bool] = None
    custom_weight: Optional[float] = None
    custom_notes: Optional[str] = None


class CompanyCompetencyConfigPublic(CompanyCompetencyConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competency: Optional[QualityCompetencyPublic] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class CompanyCompetencyConfigsPublic(BaseModel):
    data: List[CompanyCompetencyConfigPublic]
    pagination: Pagination
