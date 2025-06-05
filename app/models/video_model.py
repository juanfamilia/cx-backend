from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.evaluation_model import Evaluation


class Video(SQLModel, table=True):
    __tablename__ = "videos"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str

    evaluations: List["Evaluation"] = Relationship(back_populates="video")


class VideoCreate(SQLModel):
    title: str
    url: str
