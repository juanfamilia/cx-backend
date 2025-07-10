from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.campaign_model import Campaign, CampaignPublic
from app.models.user_model import User, UserPublic
from app.types.pagination import Pagination


class CampaignGoalsEvaluatorBase(SQLModel):
    evaluator_id: int = Field(foreign_key="users.id")
    campaign_id: int = Field(foreign_key="campaigns.id")
    goal: int = Field(default=0)


class CampaignGoalsEvaluator(CampaignGoalsEvaluatorBase, table=True):
    __tablename__ = "campaign_goals_evaluators"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    evaluator: User = Relationship(
        back_populates="campaign_goals_evaluators",
        sa_relationship_kwargs={"lazy": "noload"},
    )
    campaign: Campaign = Relationship(
        back_populates="campaign_goals_evaluators",
        sa_relationship_kwargs={"lazy": "noload"},
    )


class CampaignGoalsEvaluatorUpdate(SQLModel):
    goal: int | None = Field(default=None)


class CampaignGoalsEvaluatorPublic(CampaignGoalsEvaluatorBase):
    id: int
    evaluator: UserPublic | None = None
    campaign: CampaignPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class CampaignGoalsEvaluatorsPublic(BaseModel):
    data: list[CampaignGoalsEvaluatorPublic]
    pagination: Pagination
