from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, SQLModel, func, Text


class EvaluationEventTypeEnum(str, Enum):
    COMPLAINT = "complaint"
    EMOTIONAL_PEAK = "emotional_peak"
    SALES_SIGNAL = "sales_signal"
    OBJECTION = "objection"
    RESOLUTION = "resolution"
    COMPLIANCE_RISK = "compliance_risk"
    OTHER = "other"


class EvaluationEventBase(SQLModel):
    evaluation_id: int = Field(foreign_key="evaluations.id", index=True)
    event_type: EvaluationEventTypeEnum
    timestamp_seconds: float = Field(index=True)
    severity: int = Field(default=1, ge=1, le=5)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    source: str = Field(default="system")


class EvaluationEvent(EvaluationEventBase, table=True):
    __tablename__ = "evaluation_events"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )


class EvaluationEventCreate(SQLModel):
    event_type: EvaluationEventTypeEnum
    timestamp_seconds: float
    severity: int = Field(default=1, ge=1, le=5)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_text: Optional[str] = None
    source: str = "manual"


class EvaluationEventPublic(EvaluationEventBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EvaluationEventsPublic(BaseModel):
    data: list[EvaluationEventPublic]
    total: int
