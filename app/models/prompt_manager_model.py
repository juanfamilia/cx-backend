from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from sqlalchemy import JSON
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.company_model import Company


class PromptManagerBase(SQLModel):
    """Base model for AI prompt management per company"""
    company_id: int = Field(foreign_key="companies.id")
    prompt_name: str = Field(max_length=100, description="Name/identifier for the prompt")
    prompt_type: str = Field(
        default="dual_analysis",
        description="Type: dual_analysis, executive_only, operative_only, custom"
    )
    system_prompt: str = Field(description="System prompt for AI analysis")
    is_active: bool = Field(default=True, description="Whether this prompt is currently active")
    metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional configuration (temperature, max_tokens, etc.)"
    )


class PromptManagerCreate(PromptManagerBase):
    """Schema for creating a new prompt"""
    pass


class PromptManagerUpdate(SQLModel):
    """Schema for updating an existing prompt"""
    prompt_name: str | None = None
    prompt_type: str | None = None
    system_prompt: str | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class PromptManager(PromptManagerBase, table=True):
    """Database table for prompt management"""
    __tablename__ = "prompt_managers"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)
    
    company: "Company" = Relationship(
        back_populates="prompts", sa_relationship_kwargs={"lazy": "noload"}
    )


class PromptManagerPublic(PromptManagerBase):
    """Public schema for prompt responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class PromptManagersPublic(SQLModel):
    """Paginated response for prompts"""
    data: list[PromptManagerPublic]
    total: int
