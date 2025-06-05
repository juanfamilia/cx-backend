from datetime import datetime
from typing import List
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.campaign_model import Campaign, CampaignPublic
from app.models.campaign_user_model import CampaignUserPublic
from app.models.zone_model import Zone, ZonePublic
from app.types.pagination import Pagination


class CampaignZoneBase(SQLModel):
    campaign_id: int | None = Field(default=None, foreign_key="campaigns.id")
    zone_id: int | None = Field(default=None, foreign_key="zones.id")


class CampaignZone(CampaignZoneBase, table=True):
    __tablename__ = "campaign_zones"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    campaign: Campaign = Relationship(
        back_populates="campaigns_zone", sa_relationship_kwargs={"lazy": "noload"}
    )
    zone: Zone = Relationship(
        back_populates="campaigns_zone", sa_relationship_kwargs={"lazy": "noload"}
    )


class CampaignZonePublic(CampaignZoneBase):
    id: int
    campaign: CampaignPublic | None = None
    zone: ZonePublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class CampaignZonesPublic(BaseModel):
    data: List[CampaignZonePublic]
    pagination: Pagination


class createCampaignZone(BaseModel):
    campaign_id: int
    zone_ids: list[int]


class currentAssignedCampaign(BaseModel):
    by_user: List[CampaignUserPublic]
    by_zone: List[CampaignZonePublic]
