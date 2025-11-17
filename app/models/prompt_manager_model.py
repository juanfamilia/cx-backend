from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from sqlalchemy import JSON
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.company_model import Company

class PromptManagerBase(SQLModel):
    """Base model for AI prompt management per company"""
    name: str = Field(max_length=255, description="Name of the prompt")
    description: str | None = Field(default=None, description="Description of the prompt")
    template: str = Field(description="Prompt template with variables")
    category: str = Field(max_length=100, description="Category of the prompt")
    variables: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Variables used in the template"
    )
    is_active: bool = Field(default=True, description="Whether this prompt is currently active")
    version: int = Field(default=1, description="Version number of the prompt")
    company_id: int = Field(foreign_key="companies.id")

class PromptManagerCreate(PromptManagerBase):
    """Schema for creating a new prompt"""
    pass

class PromptManagerUpdate(SQLModel):
    """Schema for updating an existing prompt"""
    name: str | None = None
    description: str | None = None
    template: str | None = None
    category: str | None = None
    variables: dict[str, Any] | None = None
    is_active: bool | None = None
    version: int | None = None

class PromptManager(PromptManagerBase, table=True):
    """Database table for prompt management"""
    __tablename__ = "prompts"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    # deleted_at removed - not in current DB schema
    company: "Company" = Relationship(
        back_populates="prompts", sa_relationship_kwargs={"lazy": "noload"}
    )

class PromptManagerPublic(PromptManagerBase):
    """Public schema for prompt responses"""
    id: int
    created_at: datetime
    updated_at: datetime

class PromptManagersPublic(SQLModel):
    """Paginated response for prompts"""
    data: list[PromptManagerPublic]
    total: int
