from datetime import datetime
from typing import List
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.campaign_model import Campaign, CampaignPublic
from app.models.user_model import User, UserPublic
from app.types.pagination import Pagination


class CampaignUserBase(SQLModel):
    campaign_id: int | None = Field(default=None, foreign_key="campaigns.id")
    user_id: int | None = Field(default=None, foreign_key="users.id")


class CampaignUser(CampaignUserBase, table=True):
    __tablename__ = "campaign_users"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    campaign: Campaign = Relationship(
        back_populates="campaigns_user", sa_relationship_kwargs={"lazy": "noload"}
    )
    user: User = Relationship(
        back_populates="campaigns_user", sa_relationship_kwargs={"lazy": "noload"}
    )


class CampaignUserPublic(CampaignUserBase):
    id: int
    campaign: CampaignPublic | None = None
    user: UserPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class CampaignUsersPublic(BaseModel):
    data: List[CampaignUserPublic]
    pagination: Pagination


class createCampaignUser(BaseModel):
    campaign_id: int
    user_ids: list[int]
