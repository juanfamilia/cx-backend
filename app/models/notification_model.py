from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.evaluation_model import Evaluation, EvaluationPublic, StatusEnum
from app.models.user_model import User, UserPublic


class NotificationBase(SQLModel):
    user_id: int | None = Field(default=None, foreign_key="users.id")
    evaluation_id: int | None = Field(default=None, foreign_key="evaluations.id")
    status: StatusEnum
    read: bool = Field(default=False)
    comment: str | None = Field(nullable=True)


class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    user: User = Relationship(
        back_populates="notifications", sa_relationship_kwargs={"lazy": "noload"}
    )
    evaluation: Evaluation = Relationship(
        back_populates="notifications", sa_relationship_kwargs={"lazy": "noload"}
    )


class NotificationUpdate(SQLModel):
    read: bool = Field(default=False)


class NotificationPublic(NotificationBase):
    id: int
    user: UserPublic | None = None
    evaluation: EvaluationPublic | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
