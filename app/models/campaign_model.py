from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List
from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from app.models.campaign_user_model import CampaignUser
    from app.models.campaign_zone_model import CampaignZone
    from app.models.evaluation_model import Evaluation
    from app.models.campaign_goals_evaluator_model import CampaignGoalsEvaluator

from app.models.company_model import Company
from app.models.survey_forms_model import SurveyForm, SurveyFormPublic
from app.types.pagination import Pagination


class ChannelType(str, Enum):
    presencial = "presencial"
    telefonico = "telefonico"
    online = "online"


class CampaignBase(SQLModel):
    company_id: int | None = Field(default=None, foreign_key="companies.id")
    name: str
    objective: str | None = Field(nullable=True)
    date_start: datetime
    date_end: datetime
    channel: ChannelType = ChannelType.presencial
    survey_id: int | None = Field(default=None, foreign_key="survey_forms.id")
    notes: str | None = Field(nullable=True)
    goal: int = Field(default=0)


class CampaignUpdate(SQLModel):
    name: str | None = Field(default=None)
    objective: str | None = Field(default=None)
    date_start: datetime | None = Field(default=None)
    date_end: datetime | None = Field(default=None)
    channel: ChannelType | None = Field(default=None)
    survey_id: int | None = Field(default=None)
    notes: str | None = Field(default=None)
    goal: int | None = Field(default=None)


class Campaign(CampaignBase, table=True):
    __tablename__ = "campaigns"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    company: Company = Relationship(
        back_populates="campaigns", sa_relationship_kwargs={"lazy": "noload"}
    )
    survey: SurveyForm = Relationship(
        back_populates="campaigns", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaigns_user: List["CampaignUser"] = Relationship(
        back_populates="campaign", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaigns_zone: List["CampaignZone"] = Relationship(
        back_populates="campaign", sa_relationship_kwargs={"lazy": "noload"}
    )
    evaluations: List["Evaluation"] = Relationship(
        back_populates="campaign", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaign_goals_evaluators: List["CampaignGoalsEvaluator"] = Relationship(
        back_populates="campaign", sa_relationship_kwargs={"lazy": "noload"}
    )


class CampaignPublic(CampaignBase):
    id: int
    survey: SurveyFormPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CampaignsPublic(BaseModel):
    data: List[CampaignPublic]
    pagination: Pagination
