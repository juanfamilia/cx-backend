from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func


from app.models.campaign_model import Campaign, CampaignPublic
from app.models.survey_model import SurveyAspect, SurveyAspectPublic
from app.models.video_model import Video


class StatusEnum(str, Enum):
    SEND = "enviado"
    UPDATED = "atualizado"
    APROVED = "aprovado"
    REJECTED = "rechazado"


# ----------- EVALUATION -----------
class EvaluationBase(SQLModel):
    campaigns_id: int | None = Field(default=None, foreign_key="campaigns.id")
    video_id: int | None = Field(default=None, foreign_key="videos.id")
    user_id: int | None = Field(default=None, foreign_key="users.id")
    location: Optional[str] = Field(nullable=True, default=None)
    evaluated_collaborator: str = Field(nullable=True)
    status: StatusEnum = Field(default=StatusEnum.SEND)


class Evaluation(EvaluationBase, table=True):
    __tablename__ = "evaluations"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    video: Video = Relationship(back_populates="evaluations")
    campaign: Campaign = Relationship(
        back_populates="evaluations", sa_relationship_kwargs={"lazy": "noload"}
    )
    evaluation_answers: List["EvaluationAnswer"] = Relationship(
        back_populates="evaluation", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationCreate(EvaluationBase):
    evaluation_answers: List["EvaluationAnswerBase"]


class EvaluationUpdate(SQLModel):
    location: Optional[str] = None
    evaluated_collaborator: Optional[str] = None
    status: Optional[StatusEnum] = StatusEnum.UPDATED
    evaluation_answers: Optional[List["EvaluationAnswerUpdate"]] = None
    video_id: Optional[int] = None


class EvaluationPublic(EvaluationBase):
    id: int
    video: Video | None = None
    campaign: CampaignPublic | None = None
    evaluation_answers: List["EvaluationAnswerPublic"] | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


# ----------- ANSWERS -----------
class EvaluationAnswerBase(SQLModel):
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id")
    aspect_id: int | None = Field(default=None, foreign_key="survey_aspects.id")
    value_number: Optional[int] = Field(default=None, nullable=True)
    value_boolean: Optional[bool] = Field(default=None, nullable=True)
    comment: str | None = Field(default=None, nullable=True)


class EvaluationAnswer(EvaluationAnswerBase, table=True):
    __tablename__ = "evaluation_answers"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    evaluation: "Evaluation" = Relationship(
        back_populates="evaluation_answers", sa_relationship_kwargs={"lazy": "noload"}
    )
    aspect: SurveyAspect = Relationship(
        back_populates="evaluation_answers", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationAnswerUpdate(SQLModel):
    id: int
    value_number: Optional[int] = None
    value_boolean: Optional[bool] = None
    comment: Optional[str] = None


class EvaluationAnswerPublic(EvaluationAnswerBase):
    id: int
    aspect: SurveyAspectPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
