from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel, EmailStr
from sqlmodel import Relationship, SQLModel, Field, Column, DateTime, func

from app.models.company_model import Company
from app.types.pagination import Pagination


if TYPE_CHECKING:
    from app.models.user_zone_model import UserZone
    from app.models.campaign_user_model import CampaignUser
    from app.models.evaluation_model import Evaluation
    from app.models.notification_model import Notification
    from app.models.dashboard_config_model import DashboardConfig
    from app.models.widget_model import UserDashboardWidget
    from app.models.onboarding_model import OnboardingStatus


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CivilStatusEnum(str, Enum):
    SINGLE = "soltero"
    MARRIED = "casado"
    DIVORCED = "divorciado"
    WIDOWED = "viudo"
    SEPARATED = "separado"


class SocioeconomicEnum(str, Enum):
    LOW = "bajo"
    MEDIUM = "medio"
    HIGH = "alto"


# Shared properties
class UserBase(SQLModel):
    role: int = 3
    first_name: str
    last_name: str
    gender: GenderEnum = GenderEnum.MALE
    birthdate: datetime | None = Field(default=None, nullable=True)
    civil_status: CivilStatusEnum = Field(default=CivilStatusEnum.SINGLE, nullable=True)
    socioeconomic: SocioeconomicEnum = Field(
        default=SocioeconomicEnum.LOW, nullable=True
    )
    inclusivity: str = Field(default=None, nullable=True)
    email: EmailStr = Field(nullable=False, unique=True, index=True)
    company_id: int | None = Field(default=None, foreign_key="companies.id")


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(nullable=False, min_length=8, max_length=40)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    gender: GenderEnum | None = Field(default=None)
    birthdate: datetime | None = Field(default=None)
    civil_status: CivilStatusEnum | None = Field(default=None)
    socioeconomic: SocioeconomicEnum | None = Field(default=None)
    inclusivity: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    company_id: int | None = Field(default=None)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    company: Company = Relationship(
        back_populates="employees", sa_relationship_kwargs={"lazy": "noload"}
    )
    user_zones: List["UserZone"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaigns_user: List["CampaignUser"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    evaluations: List["Evaluation"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    notifications: List["Notification"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    campaign_goals_evaluators: List["CampaignGoalsEvaluator"] = Relationship(
        back_populates="evaluator", sa_relationship_kwargs={"lazy": "noload"}
    )
    dashboard_configs: List["DashboardConfig"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    dashboard_widgets: List["UserDashboardWidget"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload"}
    )
    onboarding_status: Optional["OnboardingStatus"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "noload", "uselist": False}
    )


class UserPublic(UserBase):
    id: int
    company: Optional[Company] = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class UsersPublic(BaseModel):
    data: list[UserPublic]
    pagination: Pagination


from app.models.campaign_goals_evaluator_model import CampaignGoalsEvaluator
