from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.clip_model import Clip


class InsightTypeEnum(str, Enum):
    SUMMARY = "summary"
    ALERT = "alert"
    RECOMMENDATION = "recommendation"


class InsightPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InsightBase(SQLModel):
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    # summary | alert | recommendation
    type: InsightTypeEnum = Field(index=True)
    title: str
    description: str
    # low | medium | high
    priority: InsightPriorityEnum | None = Field(default=None, index=True)
    score: float | None = Field(default=None)
    suggested_actions: list[str] = Field(
        sa_column=Column(ARRAY(String), nullable=True), default_factory=list
    )
    is_read: bool = Field(default=False)


class Insight(InsightBase, table=True):
    __tablename__ = "insights"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    clips: List["Clip"] = Relationship(
        back_populates="insight", sa_relationship_kwargs={"lazy": "noload"}
    )


class InsightCreate(InsightBase):
    pass


class InsightUpdate(SQLModel):
    type: InsightTypeEnum | None = None
    title: str | None = None
    description: str | None = None
    priority: InsightPriorityEnum | None = None
    score: float | None = None
    suggested_actions: list[str] | None = None
    is_read: bool | None = None


class InsightPublic(InsightBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class InsightsPublic(BaseModel):
    data: List[InsightPublic]
    pagination: Pagination
