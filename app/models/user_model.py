from datetime import datetime
from enum import Enum
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Column, DateTime, func


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# Shared properties
class UserBase(SQLModel):
    role: int = 3
    first_name: str
    last_name: str
    gender: GenderEnum = GenderEnum.MALE
    email: EmailStr = Field(nullable=False, unique=True, index=True)


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
    email: EmailStr | None = Field(default=None)


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


class UserPublic(UserBase):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None
