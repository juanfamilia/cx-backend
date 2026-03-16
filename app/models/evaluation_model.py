from datetime import datetime, date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, Integer, Relationship, SQLModel, func, Date
from sqlalchemy.dialects.postgresql import ARRAY


from app.models.campaign_model import Campaign, CampaignPublic
from app.models.survey_model import SurveyAspect, SurveyAspectPublic
from app.models.user_model import User, UserPublic
from app.models.video_model import Video
from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.notification_model import Notification
    from app.models.evaluation_analysis_model import EvaluationAnalysis
    from app.models.transcript_segment_model import TranscriptSegment


class InteractionTypeEnum(str, Enum):
    """Type of customer interaction"""
    IN_PERSON = "presencial"
    CALL_CENTER = "callcenter"
    WHATSAPP = "whatsapp"
    VIDEO_CALL = "videollamada"
    OTHER = "otro"


class StatusEnum(str, Enum):
    SEND = "enviado"
    EDIT = "editar"
    UPDATED = "actualizado"
    APROVED = "aprobado"
    REJECTED = "rechazado"


# ----------- EVALUATION -----------
class EvaluationBase(SQLModel):
    campaigns_id: int | None = Field(default=None, foreign_key="campaigns.id")
    video_id: int | None = Field(default=None, foreign_key="videos.id")
    user_id: int | None = Field(default=None, foreign_key="users.id")
    location: Optional[str] = Field(nullable=True, default=None)
    evaluated_collaborator: str = Field(nullable=True)
    status: StatusEnum = Field(default=StatusEnum.SEND)
    visited_zones: List[int] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True), default_factory=list
    )
    
    # ========== NEW METADATA FIELDS ==========
    # Location/Branch info
    country: Optional[str] = Field(default=None, description="Country code or name")
    branch_id: Optional[str] = Field(default=None, description="Branch identifier")
    branch_name: Optional[str] = Field(default=None, description="Branch display name")
    
    # Interaction details
    interaction_type: Optional[InteractionTypeEnum] = Field(
        default=InteractionTypeEnum.IN_PERSON,
        description="Type of interaction"
    )
    interaction_date: Optional[date] = Field(
        sa_column=Column(Date, nullable=True),
        default=None,
        description="Date of the interaction"
    )
    interaction_duration: Optional[int] = Field(
        default=None,
        description="Duration of interaction in seconds"
    )
    
    # Customer info
    customer_segment: Optional[str] = Field(default=None, description="Customer segment (premium, standard, etc)")
    product_consulted: Optional[str] = Field(default=None, description="Product or service discussed")
    
    # ========== AI-EXTRACTED FIELDS ==========
    # These are populated after AI analysis
    customer_emotion: Optional[str] = Field(default=None, description="Detected customer emotion")
    agent_emotion: Optional[str] = Field(default=None, description="Detected agent emotion")
    problem_resolved: Optional[bool] = Field(default=None, description="Was the problem resolved?")
    product_offered: Optional[bool] = Field(default=None, description="Was a product offered?")
    risk_of_churn: Optional[int] = Field(default=None, description="Risk of churn score 0-100")
    service_quality_score: Optional[int] = Field(default=None, description="Service quality score 0-100")
    customer_effort_score: Optional[int] = Field(default=None, description="Customer effort score 0-100")
    nps_inferred: Optional[int] = Field(default=None, description="Inferred NPS score 0-10")
    greeting_detected: Optional[bool] = Field(default=None, description="Was a proper greeting detected?")


class Evaluation(EvaluationBase, table=True):
    __tablename__ = "evaluations"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    video: Video = Relationship(
        back_populates="evaluations", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaign: Campaign = Relationship(
        back_populates="evaluations", sa_relationship_kwargs={"lazy": "noload"}
    )
    user: User = Relationship(
        back_populates="evaluations", sa_relationship_kwargs={"lazy": "noload"}
    )
    evaluation_answers: List["EvaluationAnswer"] = Relationship(
        back_populates="evaluation", sa_relationship_kwargs={"lazy": "noload"}
    )
    notifications: List["Notification"] = Relationship(
        back_populates="evaluation", sa_relationship_kwargs={"lazy": "noload"}
    )

    analysis: "EvaluationAnalysis" = Relationship(
        back_populates="evaluation", sa_relationship_kwargs={"lazy": "noload"}
    )
    
    transcript_segments: List["TranscriptSegment"] = Relationship(
        back_populates="evaluation", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationCreate(EvaluationBase):
    evaluation_answers: List["EvaluationAnswerBase"]
    # New metadata fields can be passed at creation
    country: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    interaction_type: Optional[InteractionTypeEnum] = InteractionTypeEnum.IN_PERSON
    interaction_date: Optional[date] = None
    customer_segment: Optional[str] = None
    product_consulted: Optional[str] = None


class EvaluationUpdate(SQLModel):
    location: Optional[str] = None
    evaluated_collaborator: Optional[str] = None
    status: Optional[StatusEnum] = StatusEnum.UPDATED
    evaluation_answers: Optional[List["EvaluationAnswerUpdate"]] = None
    video_id: Optional[int] = None


class EvaluationPublic(EvaluationBase):
    id: int
    video: Video | None = None
    campaign: CampaignPublic | None = None
    evaluation_answers: List["EvaluationAnswerPublic"] | None = None
    user: UserPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class EvaluationsPublic(BaseModel):
    data: List[EvaluationPublic]
    pagination: Pagination


class StatusChangeRequest(BaseModel):
    comment: str | None = None
    status: StatusEnum


# ----------- ANSWERS -----------
class EvaluationAnswerBase(SQLModel):
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id")
    aspect_id: int | None = Field(default=None, foreign_key="survey_aspects.id")
    value_number: Optional[int] = Field(default=None, nullable=True)
    value_boolean: Optional[bool] = Field(default=None, nullable=True)
    comment: str | None = Field(default=None, nullable=True)


class EvaluationAnswer(EvaluationAnswerBase, table=True):
    __tablename__ = "evaluation_answers"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    evaluation: "Evaluation" = Relationship(
        back_populates="evaluation_answers", sa_relationship_kwargs={"lazy": "noload"}
    )
    aspect: SurveyAspect = Relationship(
        back_populates="evaluation_answers", sa_relationship_kwargs={"lazy": "noload"}
    )


class EvaluationAnswerUpdate(SQLModel):
    id: int
    value_number: Optional[int] = None
    value_boolean: Optional[bool] = None
    comment: Optional[str] = None


class EvaluationAnswerPublic(EvaluationAnswerBase):
    id: int
    aspect: SurveyAspectPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
