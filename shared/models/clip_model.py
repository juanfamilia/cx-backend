"""
Clip Model - Video clips extracted from evaluations
Each clip represents a key moment (verbatim) from the evaluation video
"""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional, Any
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func, JSON

if TYPE_CHECKING:
    from shared.models.evaluation_model import Evaluation


class VerbatimType(str, Enum):
    """Type of verbatim that generated this clip"""
    CRITICAL = "critical"
    NEGATIVE = "negative"
    POSITIVE = "positive"


class ClipStatus(str, Enum):
    """Processing status of the clip"""
    PENDING = "pending"          # Waiting to be processed
    PROCESSING = "processing"    # Currently being generated
    UPLOADING = "uploading"      # Uploading to Cloudflare
    READY = "ready"              # Available for playback
    FAILED = "failed"            # Generation failed
    DELETED = "deleted"          # Soft deleted


# ============ CLIP CONFIGURATION ============

class ClipConfigBase(SQLModel):
    """Configuration for clip generation per company"""
    company_id: int = Field(foreign_key="companies.id")
    
    # Duration settings (in seconds)
    critical_before: int = Field(default=10, description="Seconds before timestamp for critical verbatims")
    critical_after: int = Field(default=20, description="Seconds after timestamp for critical verbatims")
    negative_before: int = Field(default=5, description="Seconds before timestamp for negative verbatims")
    negative_after: int = Field(default=15, description="Seconds after timestamp for negative verbatims")
    positive_before: int = Field(default=5, description="Seconds before timestamp for positive verbatims")
    positive_after: int = Field(default=10, description="Seconds after timestamp for positive verbatims")
    
    # Limits
    max_clip_duration: int = Field(default=60, description="Maximum clip duration in seconds")
    max_clips_delivered: int = Field(default=5, description="Maximum clips delivered to client")
    
    is_active: bool = Field(default=True)


class ClipConfig(ClipConfigBase, table=True):
    """Database table for clip configuration"""
    __tablename__ = "clip_configs"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )


class ClipConfigPublic(ClipConfigBase):
    """Public schema for clip config"""
    id: int
    created_at: datetime
    updated_at: datetime


# ============ CLIP MODEL ============

class ClipBase(SQLModel):
    """Base model for video clips"""
    evaluation_id: int = Field(foreign_key="evaluations.id")
    
    # Cloudflare Stream reference
    cloudflare_uid: str | None = Field(default=None, description="Cloudflare Stream video UID")
    stream_url: str | None = Field(default=None, description="HLS streaming URL")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail image URL")
    
    # Verbatim data
    verbatim_type: VerbatimType = Field(description="Type: critical, negative, positive")
    verbatim_text: str = Field(description="The actual verbatim text")
    verbatim_origin: str = Field(default="cliente", description="Origin: cliente or colaborador")
    
    # Timing (in seconds from video start)
    original_timestamp: int = Field(description="Original timestamp from GPT (in seconds)")
    clip_start: int = Field(description="Clip start time in original video (seconds)")
    clip_end: int = Field(description="Clip end time in original video (seconds)")
    clip_duration: int = Field(description="Clip duration in seconds")
    
    # Prioritization
    priority_score: float = Field(default=0.0, description="Score for prioritization (higher = more important)")
    priority_rank: int | None = Field(default=None, description="Rank among clips in this evaluation")
    is_delivered: bool = Field(default=False, description="Whether this clip is in the Top N delivered to client")
    
    # Processing
    status: ClipStatus = Field(default=ClipStatus.PENDING)
    error_message: str | None = Field(default=None, description="Error message if generation failed")
    
    # Metadata
    extra_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata (IOC, IRD, CES context, etc.)"
    )


class Clip(ClipBase, table=True):
    """Database table for clips"""
    __tablename__ = "clips"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)
    
    # Relationships
    evaluation: "Evaluation" = Relationship(sa_relationship_kwargs={"lazy": "noload"})


class ClipCreate(SQLModel):
    """Schema for creating a clip (internal use)"""
    evaluation_id: int
    verbatim_type: VerbatimType
    verbatim_text: str
    verbatim_origin: str
    original_timestamp: int
    clip_start: int
    clip_end: int
    clip_duration: int
    priority_score: float = 0.0
    extra_data: dict[str, Any] | None = None


class ClipUpdate(SQLModel):
    """Schema for updating a clip"""
    cloudflare_uid: str | None = None
    stream_url: str | None = None
    thumbnail_url: str | None = None
    status: ClipStatus | None = None
    error_message: str | None = None
    priority_rank: int | None = None
    is_delivered: bool | None = None


class ClipPublic(ClipBase):
    """Public schema for clip"""
    id: int
    created_at: datetime
    updated_at: datetime


class ClipsPublic(SQLModel):
    """Paginated response for clips"""
    data: list[ClipPublic]
    total: int
    delivered_count: int  # How many are marked as delivered
