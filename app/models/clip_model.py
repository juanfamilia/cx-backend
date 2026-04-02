from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import Text
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.insight_model import Insight


class ClipBase(SQLModel):
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    # Seconds in timeline
    start_time: float
    end_time: float
    text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    # Relation to insight
    insight_id: int | None = Field(default=None, foreign_key="insights.id", index=True)
    # Semantic tag
    tag: str | None = Field(default=None, index=True)


class Clip(ClipBase, table=True):
    __tablename__ = "clips"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    insight: "Insight" | None = Relationship(
        back_populates="clips", sa_relationship_kwargs={"lazy": "noload"}
    )


class ClipCreate(ClipBase):
    pass


class ClipUpdate(SQLModel):
    start_time: float | None = None
    end_time: float | None = None
    text: str | None = None
    tag: str | None = None
    insight_id: int | None = None


class ClipPublic(ClipBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class ClipsPublic(BaseModel):
    data: list[ClipPublic]
    pagination: Pagination
