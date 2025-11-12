from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime, func, ARRAY, String

if TYPE_CHECKING:
    from app.models.user_model import User

class OnboardingStep(str, Enum):
    """Steps del proceso de onboarding"""
    PROFILE_COMPLETED = "profile_completed"
    COMPANY_CONFIGURED = "company_configured"
    FIRST_CAMPAIGN_CREATED = "first_campaign_created"
    FIRST_ZONE_CREATED = "first_zone_created"
    FIRST_USER_INVITED = "first_user_invited"
    FIRST_EVALUATION_CREATED = "first_evaluation_created"
    FIRST_VIDEO_UPLOADED = "first_video_uploaded"
    DASHBOARD_CUSTOMIZED = "dashboard_customized"
    TOUR_COMPLETED = "tour_completed"

class ProductTour(str, Enum):
    """Tours disponibles en la plataforma"""
    WELCOME_TOUR = "welcome_tour"
    DASHBOARD_TOUR = "dashboard_tour"
    CAMPAIGN_TOUR = "campaign_tour"
    EVALUATION_TOUR = "evaluation_tour"
    ANALYTICS_TOUR = "analytics_tour"

class OnboardingStatus(SQLModel, table=True):
    """Estado de onboarding por usuario"""
    __tablename__ = "onboarding_status"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    
    # Steps completados
    steps_completed: list[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    
    # Tours vistos
    tours_completed: list[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    
    # Progreso
    total_steps: int = 9  # Total de steps en OnboardingStep
    progress_percentage: int = 0
    
    # Estado
    is_completed: bool = False
    completed_at: datetime | None = None
    skipped: bool = False
    
    # Métricas de engagement
    started_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    last_interaction: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    days_to_complete: int | None = None
    
    # Relación
    user: "User" = Relationship(back_populates="onboarding_status")

class OnboardingStatusPublic(SQLModel):
    """Schema público de onboarding"""
    user_id: int
    steps_completed: list[str]
    tours_completed: list[str]
    progress_percentage: int
    is_completed: bool
    next_step: str | None  # Siguiente step sugerido
