from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func


if TYPE_CHECKING:
    from app.models.evaluation_model import EvaluationAnswer
    from app.models.survey_forms_model import SurveyForm


class AspectTypeEnum(str, Enum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIKERT = "likert"        # escala 1-5
    COMPLIANCE = "compliance"  # C / NC / CP / NA
    MEDIA = "media"          # requiere evidencia adjunta (foto/clip)


# ----------- SECTIONS -----------
class SurveySectionBase(SQLModel):
    name: str
    maximum_score: int
    order: int
    form_id: int | None = Field(default=None, foreign_key="survey_forms.id")
    # Peso relativo de la sección (0.0 – 1.0). La suma de todas las secciones
    # de un formulario debe ser 1.0. Si es None se distribuye igualmente.
    weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SurveySection(SurveySectionBase, table=True):
    __tablename__ = "survey_sections"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    form: "SurveyForm" = Relationship(back_populates="sections")
    aspects: List["SurveyAspect"] = Relationship(back_populates="section")


class SurveySectionCreate(SQLModel):
    name: str
    maximum_score: int
    order: int
    weight: Optional[float] = None
    aspects: List["SurveyAspectCreate"]


class SurveySectionPublic(BaseModel):
    id: int
    name: str
    maximum_score: int
    order: int
    weight: Optional[float] = None
    aspects: List["SurveyAspectPublic"] | None = None

    model_config = ConfigDict(from_attributes=True)


# ----------- ASPECTS -----------
class SurveyAspectBase(SQLModel):
    description: str
    type: AspectTypeEnum = AspectTypeEnum.NUMBER
    maximum_score: Optional[int] = Field(default=None)
    section_id: int | None = Field(default=None, foreign_key="survey_sections.id")
    order: int
    # Peso dentro de la sección (0.0 – 1.0). Si es None se distribuye igualmente.
    weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    # Si True, este aspecto requiere evidencia (clip/foto) para poder marcarse como C
    requires_evidence: bool = Field(default=False)


class SurveyAspect(SurveyAspectBase, table=True):
    __tablename__ = "survey_aspects"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    section: "SurveySection" = Relationship(back_populates="aspects")
    evaluation_answers: List["EvaluationAnswer"] = Relationship(
        back_populates="aspect", sa_relationship_kwargs={"lazy": "noload"}
    )


class SurveyAspectCreate(SQLModel):
    description: str
    type: AspectTypeEnum = AspectTypeEnum.NUMBER
    maximum_score: Optional[int] = None
    order: int
    weight: Optional[float] = None
    requires_evidence: bool = False


class SurveyAspectPublic(BaseModel):
    id: int
    description: str
    type: AspectTypeEnum
    maximum_score: Optional[int] = None
    order: int
    weight: Optional[float] = None
    requires_evidence: bool = False

    model_config = ConfigDict(from_attributes=True)
