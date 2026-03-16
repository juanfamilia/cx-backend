"""
Transcript Segment Model
Stores individual segments from Whisper transcription for synchronized playback
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func, Text

if TYPE_CHECKING:
    from app.models.evaluation_model import Evaluation


class TranscriptSegmentBase(SQLModel):
    """Base model for transcript segments"""
    evaluation_id: int = Field(foreign_key="evaluations.id", index=True)
    
    # Timing from Whisper
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    
    # Content
    text: str = Field(sa_column=Column(Text), description="Transcript text for this segment")
    
    # Optional: speaker identification (for future use)
    speaker: Optional[str] = Field(default=None, description="Speaker identifier if available")
    
    # Confidence from Whisper (if available)
    confidence: Optional[float] = Field(default=None, description="Transcription confidence score")


class TranscriptSegment(TranscriptSegmentBase, table=True):
    """Database table for transcript segments"""
    __tablename__ = "transcript_segments"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    
    # Embedding will be stored as JSON array for now (until pgvector is enabled)
    # When pgvector is ready, this can be migrated to Vector type
    embedding_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="JSON string of embedding vector (temporary until pgvector)"
    )
    
    # Relationships
    evaluation: "Evaluation" = Relationship(
        back_populates="transcript_segments",
        sa_relationship_kwargs={"lazy": "noload"}
    )


class TranscriptSegmentCreate(SQLModel):
    """Schema for creating a segment"""
    evaluation_id: int
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class TranscriptSegmentPublic(TranscriptSegmentBase):
    """Public schema for transcript segment"""
    id: int
    created_at: datetime


class TranscriptSegmentsPublic(BaseModel):
    """List of transcript segments"""
    data: List[TranscriptSegmentPublic]
    total: int
    duration: float  # Total duration in seconds


class TranscriptSearchResult(BaseModel):
    """Search result for transcript search"""
    segment_id: int
    evaluation_id: int
    start_time: float
    end_time: float
    text: str
    # Context from evaluation
    branch_name: Optional[str] = None
    interaction_date: Optional[datetime] = None
    # For semantic search
    similarity_score: Optional[float] = None


class TranscriptSearchResponse(BaseModel):
    """Response for transcript search"""
    results: List[TranscriptSearchResult]
    total: int
    query: str
