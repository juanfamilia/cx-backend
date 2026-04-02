from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel
from sqlalchemy import Text
from sqlmodel import Column, DateTime, Field, SQLModel, func

from app.types.pagination import Pagination


class PromptTypeEnum(str, Enum):
    EVENT_EXTRACTION = "event_extraction"
    SCORING = "scoring"
    INSIGHTS = "insights"


class PromptBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    # event_extraction | scoring | insights
    type: str = Field(index=True)
    # Prompt content (LLM instructions/rules)
    content: str = Field(sa_column=Column(Text, nullable=False))
    # Tenant scope
    company_id: int = Field(foreign_key="companies.id", index=True)
    # Versioning/activation
    version: int = Field(default=1)
    is_active: bool = Field(default=True, index=True)


class Prompt(PromptBase, table=True):
    __tablename__ = "prompts"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)


class PromptCreate(PromptBase):
    pass


class PromptUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    type: str | None = None
    content: str | None = None
    version: int | None = None
    is_active: bool | None = None


class PromptPublic(PromptBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class PromptsPublic(BaseModel):
    data: List[PromptPublic]
    pagination: Pagination
