from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from sqlalchemy import JSON
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from shared.models.company_model import Company

class PromptManagerBase(SQLModel):
    """Base model for AI prompt management per company"""
    name: str = Field(max_length=255, description="Name of the prompt")
    description: Optional[str] = Field(default=None, description="Description of the prompt")
    template: str = Field(description="Prompt template with variables")
    category: str = Field(max_length=100, description="Category of the prompt")
    variables: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Variables used in the template (list of variable names)"
    )
    is_active: bool = Field(default=True, description="Whether this prompt is currently active")
    version: int = Field(default=1, description="Version number of the prompt")
    company_id: int = Field(foreign_key="companies.id")

class PromptManagerCreate(PromptManagerBase):
    """Schema for creating a new prompt"""
    pass

class PromptManagerUpdate(SQLModel):
    """Schema for updating an existing prompt"""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    version: Optional[int] = None

class PromptManager(PromptManagerBase, table=True):
    """Database table for prompt management"""
    __tablename__ = "prompts"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
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
    data: List[PromptManagerPublic]
    total: int
