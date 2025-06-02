from datetime import datetime
from typing import TYPE_CHECKING, List
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


class SurveyFormUpdate(SQLModel):
    title: str | None = Field(default=None)


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
