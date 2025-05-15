from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, DateTime, Enum, func

from pydantic import EmailStr
from sqlmodel import Relationship, SQLModel, Field

from app.models.doctors_info_model import DoctorsInfo, DoctorsInfoPublic
from app.models.doctors_offices_model import DoctorsOffices

if TYPE_CHECKING:
    from app.models.patients_model import Patient
    from app.models.refresh_token_model import RefreshToken
    from app.models.users_key_model import UserKey
    from app.models.doctors_assigments_model import DoctorsAssigments
    from app.models.events_model import Event
    from app.models.consultations_model import Consultation


# Shared properties
class UserBase(SQLModel):
    role: int = 3
    first_name: str
    last_name: str
    gender: int = 0
    email: EmailStr = Field(nullable=False, unique=True, index=True)
    identity_number: str = Field(nullable=False, unique=True)
    country_code: str = Field(nullable=False, default="VE")


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(nullable=False, min_length=8, max_length=40)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    gender: int | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    country_code: str | None = Field(default=None)


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

    patients: list["Patient"] = Relationship(back_populates="user", cascade_delete=True)
    consultations: list["Consultation"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    user_keys: list["UserKey"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    doctors_offices: "DoctorsOffices" = Relationship(
        back_populates="user",
        cascade_delete=True,
        sa_relationship_kwargs={"lazy": "select"},
    )
    doctors_info: DoctorsInfo = Relationship(
        back_populates="user",
        cascade_delete=True,
        sa_relationship_kwargs={"lazy": "select"},
    )
    secretary_assigments: list["DoctorsAssigments"] = Relationship(
        back_populates="secretary",
        sa_relationship_kwargs={"foreign_keys": "DoctorsAssigments.secretary_id"},
    )
    doctor_assigments: list["DoctorsAssigments"] = Relationship(
        back_populates="doctor",
        sa_relationship_kwargs={"foreign_keys": "DoctorsAssigments.doctor_id"},
    )
    events: list["Event"] = Relationship(back_populates="user", cascade_delete=True)


class UserPublic(UserBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None


class UserPublicRelationships(UserPublic):
    doctors_info: DoctorsInfoPublic | None = None
    doctors_offices: DoctorsOffices | None = None
