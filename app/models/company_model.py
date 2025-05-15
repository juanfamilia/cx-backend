from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from app.models.user_model import User


class CompanyBase(SQLModel):
    name: str
    phone: str
    email: str
    address: str
    city: str
    state: str
    country: str = "DO"


class CompanyUpdate(SQLModel):
    name: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    country: str | None = Field(default=None)


class Company(CompanyBase, table=True):
    __tablename__ = "companies"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    employees: list["User"] = Relationship(back_populates="company")


class CompanyPublic(CompanyBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
