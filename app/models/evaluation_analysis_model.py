from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.evaluation_model import Evaluation


class EvaluationAnalysisBase(SQLModel):
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id")
    analysis: str
    executive_view: str | None
    operative_view: str | None


class EvaluationAnalysis(EvaluationAnalysisBase, table=True):
    __tablename__ = "evaluation_analysis"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    evaluation: Evaluation = Relationship(
        back_populates="analysis", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationAnalysisPublic(EvaluationAnalysisBase):
    id: int
    evaluation: Evaluation | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
