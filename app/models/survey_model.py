from datetime import datetime
from typing import TYPE_CHECKING, List
from enum import Enum
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.video_model import Video

if TYPE_CHECKING:
    from app.models.survey_forms_model import SurveyForm


class SurveyTypeEnum(str, Enum):
    PERSON = "person"
    PHONE = "phone"
    DIGITAL = "digital"


# ----------- SURVEY -----------
class SurveyBase(SQLModel):
    company_id: int | None = Field(default=None, foreign_key="companies.id")
    video_id: int | None = Field(default=None, foreign_key="videos.id")
    user_id: int | None = Field(default=None, foreign_key="users.id")
    evaluation_type: SurveyTypeEnum = SurveyTypeEnum.PERSON
    location: str
    evaluated_collaborator: str = Field(nullable=True)


class Survey(SurveyBase, table=True):
    __tablename__ = "surveys"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    video: Video = Relationship(back_populates="surveys")
    answers: List["SurveyAnswer"] = Relationship(
        back_populates="survey", sa_relationship_kwargs={"lazy": "selectin"}
    )


# ----------- SECTIONS -----------
class SurveySectionBase(SQLModel):
    name: str
    maximum_score: int
    order: int
    form_id: int | None = Field(default=None, foreign_key="survey_forms.id")


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
    aspects: List["SurveyAspectCreate"]


class SurveySectionPublic(BaseModel):
    id: int
    name: str
    maximum_score: int
    order: int
    aspects: List["SurveyAspectPublic"] | None = None


# ----------- ASPECTS -----------
class SurveyAspectBase(SQLModel):
    description: str
    maximum_score: int
    section_id: int | None = Field(default=None, foreign_key="survey_sections.id")
    order: int


class SurveyAspect(SurveyAspectBase, table=True):
    __tablename__ = "survey_aspects"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    section: "SurveySection" = Relationship(back_populates="aspects")
    answers: List["SurveyAnswer"] = Relationship(back_populates="aspect")


class SurveyAspectCreate(SQLModel):
    description: str
    maximum_score: int
    order: int


class SurveyAspectPublic(BaseModel):
    id: int
    description: str
    maximum_score: int
    order: int


# ----------- ANSWERS -----------
class SurveyAnswerBase(SQLModel):
    survey_id: int | None = Field(default=None, foreign_key="surveys.id")
    aspect_id: int | None = Field(default=None, foreign_key="survey_aspects.id")
    score: int
    comment: str | None = Field(default=None)


class SurveyAnswer(SurveyAnswerBase, table=True):
    __tablename__ = "survey_answers"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    survey: "Survey" = Relationship(back_populates="answers")
    aspect: "SurveyAspect" = Relationship(back_populates="answers")
