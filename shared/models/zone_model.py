from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Column, DateTime, Relationship, SQLModel, Field, func

if TYPE_CHECKING:
    from app.models.user_zone_model import UserZone
    from app.models.campaign_zone_model import CampaignZone


class ZoneBase(SQLModel):
    name: str
    value: str
    country: str = Field(default="DO")


class Zone(ZoneBase, table=True):
    __tablename__ = "zones"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    user_zones: list["UserZone"] = Relationship(back_populates="zone")
    campaigns_zone: list["CampaignZone"] = Relationship(
        back_populates="zone", sa_relationship_kwargs={"lazy": "noload"}
    )


class ZonePublic(ZoneBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
