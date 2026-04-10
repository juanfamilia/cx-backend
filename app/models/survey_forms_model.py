from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from app.models.campaign_model import Campaign

from app.types.pagination import Pagination
from app.models.survey_model import (
    SurveySection,
    SurveySectionCreate,
    SurveySectionPublic,
)


class SurveyFormBase(SQLModel):
    title: str
    company_id: int = Field(foreign_key="companies.id")
    # Versionado: version se incrementa; parent_form_id apunta al formulario origen
    # Las evaluaciones históricas mantienen su survey_id intacto al versionar.
    version: int = Field(default=1)
    parent_form_id: Optional[int] = Field(
        default=None,
        foreign_key="survey_forms.id",
        description="ID del formulario del que deriva esta versión",
    )
    is_active: bool = Field(default=True, description="Solo un formulario activo por lineage")


class SurveyFormUpdate(SQLModel):
    title: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class SurveyForm(SurveyFormBase, table=True):
    __tablename__ = "survey_forms"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    sections: List[SurveySection] = Relationship(
        back_populates="form", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaigns: List["Campaign"] = Relationship(back_populates="survey")


class SurveyFormsCreate(BaseModel):
    title: str
    sections: List[SurveySectionCreate]


class SurveyFormPublic(SurveyFormBase):
    id: int
    sections: List[SurveySectionPublic] | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SurveyFormsPublic(BaseModel):
    data: List[SurveyForm]
    pagination: Pagination
