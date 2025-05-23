from datetime import datetime
from typing import TYPE_CHECKING, List
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func


from app.models.user_model import User, UserPublic
from app.models.zone_model import Zone
from app.types.pagination import Pagination


class UserZoneBase(SQLModel):
    user_id: int = Field(foreign_key="users.id")
    zone_id: int = Field(foreign_key="zones.id")


class UserZone(UserZoneBase, table=True):
    __tablename__ = "user_zones"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    user: "User" = Relationship(
        back_populates="user_zones", sa_relationship_kwargs={"lazy": "noload"}
    )
    zone: "Zone" = Relationship(
        back_populates="user_zones", sa_relationship_kwargs={"lazy": "noload"}
    )


class UserZonePublic(UserZoneBase):
    id: int
    user: UserPublic | None = None
    zone: Zone | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class UserZonesPublic(BaseModel):
    data: list[UserZonePublic]
    pagination: Pagination


class AssignZonesRequest(BaseModel):
    user_id: int
    zone_ids: List[int]
