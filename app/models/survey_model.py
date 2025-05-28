from typing import List
from enum import Enum
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


class SurveyTypeEnum(str, Enum):
    PERSON = "person"
    PHONE = "phone"
    DIGITAL = "digital"


class Video(SQLModel, table=True):
    __tablename__ = "videos"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str

    surveys: List["Survey"] = Relationship(back_populates="video")


class Survey(SQLModel, table=True):
    __tablename__ = "surveys"
    id: int | None = Field(default=None, primary_key=True)
    video_id: int | None = Field(default=None, foreign_key="videos.id")
    user_id: int | None = Field(default=None, foreign_key="users.id")
    evaluation_type: SurveyTypeEnum = SurveyTypeEnum.PERSON
    location: str
    evaluated_collaborator: str = Field(nullable=True)

    video: "Video" = Relationship(back_populates="surveys")
    answers: List["SurveyAnswer"] = Relationship(
        back_populates="survey", sa_relationship_kwargs={"lazy": "selectin"}
    )


class SurveySection(SQLModel, table=True):
    __tablename__ = "survey_sections"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    maximum_score: int
    order: int

    aspects: List["SurveyAspect"] = Relationship(back_populates="section")


class SurveyAspect(SQLModel, table=True):
    __tablename__ = "survey_aspects"
    id: int | None = Field(default=None, primary_key=True)
    description: str
    maximum_score: int
    section_id: int | None = Field(default=None, foreign_key="survey_sections.id")
    order: int

    section: "SurveySection" = Relationship(back_populates="aspects")
    answers: List["SurveyAnswer"] = Relationship(back_populates="aspect")


class SurveyAnswer(SQLModel, table=True):
    __tablename__ = "survey_answers"
    id: int | None = Field(default=None, primary_key=True)
    survey_id: int | None = Field(default=None, foreign_key="surveys.id")
    aspect_id: int | None = Field(default=None, foreign_key="survey_aspects.id")
    score: int
    comment: str | None = Field(default=None)

    survey: "Survey" = Relationship(back_populates="answers")
    aspect: "SurveyAspect" = Relationship(back_populates="answers")


class SurveyAspectPublic(BaseModel):
    id: int
    description: str
    maximum_score: int
    order: int


class SurveySectionPublic(BaseModel):
    id: int
    name: str
    maximum_score: int
    order: int
    aspects: List[SurveyAspectPublic]
