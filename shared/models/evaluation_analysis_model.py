from datetime import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Relationship, func

from shared.models.evaluation_model import Evaluation


class EvaluationAnalysisBase(SQLModel):
    evaluation_id: Optional[int] = Field(default=None, foreign_key="evaluations.id")
    analysis: str
    executive_view: Optional[str] = None
    operative_view: Optional[str] = None
    sentiment: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))


class EvaluationAnalysis(EvaluationAnalysisBase, table=True):
    __tablename__ = "evaluation_analysis"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    evaluation: Optional[Evaluation] = Relationship(
        back_populates="analysis", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationAnalysisPublic(EvaluationAnalysisBase):
    id: int
    evaluation: Optional[Evaluation] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
