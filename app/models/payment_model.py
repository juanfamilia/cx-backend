from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.models.company_model import Company


class PaymentBase(SQLModel):
    company_id: int | None = Field(default=None, foreign_key="companies.id")
    amount: int
    date: datetime
    description: str | None = Field(default=None)
    valid_before: datetime


class PaymentUpdate(SQLModel):
    amount: int | None = Field(default=None)
    date: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    valid_before: datetime | None = Field(default=None)


class Payment(PaymentBase, table=True):
    __tablename__ = "payments"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    company: Company = Relationship(
        back_populates="payments", sa_relationship_kwargs={"lazy": "noload"}
    )


class PaymentPublic(PaymentBase):
    id: int
    company: Company | None = None
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
