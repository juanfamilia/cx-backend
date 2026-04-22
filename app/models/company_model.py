from datetime import datetime
from typing import TYPE_CHECKING, List

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.payment_model import Payment
    from app.models.campaign_model import Campaign
    from app.models.industry_model import Industry


class CompanyBase(SQLModel):
    name: str
    phone: str
    email: str
    address: str
    state: str
    country: str = "DO"
    industry_id: int | None = Field(
        default=None, foreign_key="industries.id", index=True
    )
    # Siete InS (investigación cualitativa / focus): lo activa rol 0 por empresa.
    siete_ins_enabled: bool = Field(default=False)
    # Siete Field (control de levantamiento / CSV-ready).
    siete_field_enabled: bool = Field(default=False)
    # Siete Clever (analítica cuantitativa reproducible).
    siete_clever_enabled: bool = Field(default=False)

    @field_validator("industry_id", mode="before")
    @classmethod
    def industry_id_zero_is_none(cls, v: int | None) -> int | None:
        """UI / selects suelen mandar 0 como vacío; en BD la FK no admite 0."""
        if v == 0:
            return None
        return v


class CompanyUpdate(SQLModel):
    name: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    state: str | None = Field(default=None)
    country: str | None = Field(default=None)
    industry_id: int | None = Field(default=None)
    siete_ins_enabled: bool | None = Field(default=None)
    siete_field_enabled: bool | None = Field(default=None)
    siete_clever_enabled: bool | None = Field(default=None)

    @field_validator("industry_id", mode="before")
    @classmethod
    def industry_id_zero_is_none(cls, v: int | None) -> int | None:
        if v == 0:
            return None
        return v


class Company(CompanyBase, table=True):
    __tablename__ = "companies"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)

    employees: list["User"] = Relationship(back_populates="company")
    payments: list["Payment"] = Relationship(back_populates="company")
    campaigns: list["Campaign"] = Relationship(back_populates="company")
    industry: "Industry" = Relationship(
        back_populates="companies", sa_relationship_kwargs={"lazy": "noload"}
    )


class CompanyPublic(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class CompaniesPublic(BaseModel):
    data: List[CompanyPublic]
    pagination: Pagination
