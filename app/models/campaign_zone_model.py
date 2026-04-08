from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.campaign_model import Campaign, CampaignPublic, ChannelType
from app.models.zone_model import Zone, ZonePublic
from app.types.pagination import Pagination


class CampaignForAssignmentList(BaseModel):
    """Campaña sin `survey` anidado: evita grafos enormes y JSON no estándar (p. ej. NaN) en el cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None = None
    name: str
    objective: str | None = None
    date_start: datetime
    date_end: datetime
    channel: ChannelType
    survey_id: int | None = None
    notes: str | None = None
    goal: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AssignedViaUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int | None = None
    user_id: int | None = None
    campaign: CampaignForAssignmentList | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AssignedViaZone(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int | None = None
    zone_id: int | None = None
    campaign: CampaignForAssignmentList | None = None
    zone: ZonePublic | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


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
    model_config = ConfigDict(from_attributes=True)

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
    by_user: List[AssignedViaUser]
    by_zone: List[AssignedViaZone]
