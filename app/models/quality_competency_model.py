"""
Quality Competency catalog (catálogo global operativo).

Una QualityCompetency es una competencia observable y medible en una
interacción cliente-agente (p. ej. "GREETING_STANDARD", "ACTIVE_LISTENING",
"PROBLEM_RESOLUTION"). Cada competencia está anclada a una o más
dimensiones de marcos reconocidos mediante CompetencyFrameworkRef.

Los CompetencyIndicator son señales positivas o negativas observables
que ayudan tanto al auditor humano como al modelo IA a decidir el
cumplimiento de la competencia.

El campo `ai_field_hint` permite mapear la competencia a un atributo
de Evaluation extraído por IA (p. ej. "greeting_detected") para que el
Gap Analysis compare humano vs IA de manera explícita.

Referencia: ver docs/METHODOLOGY.md § 3 y § 5.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

# Runtime imports: CompetencyFrameworkRefPublic referencia FrameworkDimensionPublic.
# Si solo va en TYPE_CHECKING, Pydantic no puede resolver el forward ref en
# model_rebuild() (NameError en deploy Python 3.13).
from app.models.framework_model import FrameworkDimension, FrameworkDimensionPublic

if TYPE_CHECKING:
    from app.models.industry_template_model import IndustryTemplate
    from app.models.company_competency_config_model import CompanyCompetencyConfig


class CompetencyCategoryEnum(str, Enum):
    OPENING = "OPENING"
    ATTENTION = "ATTENTION"
    RESOLUTION = "RESOLUTION"
    VALUE = "VALUE"
    EFFORT = "EFFORT"
    CLOSURE = "CLOSURE"
    COMPLIANCE_EMOTIONAL = "COMPLIANCE_EMOTIONAL"


class CompetencyMeasurementType(str, Enum):
    BOOLEAN = "boolean"
    LIKERT = "likert"
    NUMBER = "number"


class IndicatorTypeEnum(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


# ----------- COMPETENCIA -----------

class QualityCompetencyBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=96)
    name: str = Field(max_length=128)
    category: CompetencyCategoryEnum = Field(default=CompetencyCategoryEnum.ATTENTION)
    definition: Optional[str] = Field(default=None)
    measurement_type: CompetencyMeasurementType = Field(
        default=CompetencyMeasurementType.BOOLEAN
    )
    default_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    ai_field_hint: Optional[str] = Field(default=None, max_length=96)
    is_active: bool = Field(default=True)


class QualityCompetency(QualityCompetencyBase, table=True):
    __tablename__ = "quality_competencies"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    indicators: List["CompetencyIndicator"] = Relationship(
        back_populates="competency", sa_relationship_kwargs={"lazy": "noload"}
    )
    framework_refs: List["CompetencyFrameworkRef"] = Relationship(
        back_populates="competency", sa_relationship_kwargs={"lazy": "noload"}
    )
    industry_templates: List["IndustryTemplate"] = Relationship(
        back_populates="competency", sa_relationship_kwargs={"lazy": "noload"}
    )
    company_configs: List["CompanyCompetencyConfig"] = Relationship(
        back_populates="competency", sa_relationship_kwargs={"lazy": "noload"}
    )


class QualityCompetencyCreate(SQLModel):
    code: str
    name: str
    category: CompetencyCategoryEnum = CompetencyCategoryEnum.ATTENTION
    definition: Optional[str] = None
    measurement_type: CompetencyMeasurementType = CompetencyMeasurementType.BOOLEAN
    default_weight: float = 1.0
    ai_field_hint: Optional[str] = None
    is_active: bool = True


class QualityCompetencyUpdate(SQLModel):
    name: Optional[str] = None
    category: Optional[CompetencyCategoryEnum] = None
    definition: Optional[str] = None
    measurement_type: Optional[CompetencyMeasurementType] = None
    default_weight: Optional[float] = None
    ai_field_hint: Optional[str] = None
    is_active: Optional[bool] = None


class QualityCompetencyPublic(QualityCompetencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicators: Optional[List["CompetencyIndicatorPublic"]] = None
    framework_refs: Optional[List["CompetencyFrameworkRefPublic"]] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class QualityCompetenciesPublic(BaseModel):
    data: List[QualityCompetencyPublic]
    pagination: Pagination


# ----------- INDICADOR (positivo / negativo) -----------

class CompetencyIndicatorBase(SQLModel):
    competency_id: int = Field(foreign_key="quality_competencies.id", index=True)
    indicator_type: IndicatorTypeEnum = Field(default=IndicatorTypeEnum.POSITIVE)
    description: str
    detection_hint: Optional[str] = Field(default=None)
    order: int = Field(default=0)


class CompetencyIndicator(CompetencyIndicatorBase, table=True):
    __tablename__ = "competency_indicators"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    competency: QualityCompetency = Relationship(
        back_populates="indicators", sa_relationship_kwargs={"lazy": "noload"}
    )


class CompetencyIndicatorCreate(SQLModel):
    competency_id: int
    indicator_type: IndicatorTypeEnum = IndicatorTypeEnum.POSITIVE
    description: str
    detection_hint: Optional[str] = None
    order: int = 0


class CompetencyIndicatorUpdate(SQLModel):
    indicator_type: Optional[IndicatorTypeEnum] = None
    description: Optional[str] = None
    detection_hint: Optional[str] = None
    order: Optional[int] = None


class CompetencyIndicatorPublic(CompetencyIndicatorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# ----------- REFERENCIA A MARCO (M:N) -----------

class CompetencyFrameworkRefBase(SQLModel):
    competency_id: int = Field(foreign_key="quality_competencies.id", index=True)
    framework_dimension_id: int = Field(
        foreign_key="quality_framework_dimensions.id", index=True
    )
    notes: Optional[str] = Field(default=None)


class CompetencyFrameworkRef(CompetencyFrameworkRefBase, table=True):
    __tablename__ = "competency_framework_refs"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))

    competency: QualityCompetency = Relationship(
        back_populates="framework_refs", sa_relationship_kwargs={"lazy": "noload"}
    )
    dimension: "FrameworkDimension" = Relationship(
        back_populates="competency_refs", sa_relationship_kwargs={"lazy": "noload"}
    )


class CompetencyFrameworkRefCreate(SQLModel):
    competency_id: int
    framework_dimension_id: int
    notes: Optional[str] = None


class CompetencyFrameworkRefPublic(CompetencyFrameworkRefBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dimension: Optional["FrameworkDimensionPublic"] = None
    created_at: Optional[datetime]


QualityCompetencyPublic.model_rebuild()
