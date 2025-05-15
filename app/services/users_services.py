from typing import List
from fastapi import Depends, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.security import get_password_hash
from app.models.user_model import (
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils.exeptions import NotFoundException


async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=100),
) -> List[UserPublic]:

    statement = select(User).where(User.deleted_at == None).offset(offset).limit(limit)
    result = await session.execute(statement)
    db_users = result.scalars().all()

    if not db_users:
        raise NotFoundException("Users not found")

    return [UserPublic.model_validate(user) for user in db_users]


async def get_user(session: AsyncSession, user_id: int) -> UserPublic:

    db_user = await session.get(User, user_id)

    if not db_user:
        raise NotFoundException("User not found")

    return UserPublic.model_validate(db_user)


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User:

    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    db_user = result.scalars().first()

    if not db_user:
        raise NotFoundException("User not found by email")

    return db_user


async def create_user(session: AsyncSession, user: UserCreate) -> UserPublic:
    hashed_password = get_password_hash(user.password)

    db_user = User(
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        identity_number=user.identity_number,
        email=user.email,
        hashed_password=hashed_password,
    )

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return UserPublic.model_validate(db_user)


async def update_user(
    session: AsyncSession, user_id: int, user_update: UserUpdate
) -> UserPublic:
    db_user = await get_user(session, user_id)

    user_data = user_update.model_dump(exclude_unset=True)
    extra_data = {}

    if user_update.password is not None:
        extra_data["hashed_password"] = get_password_hash(user_update.password)

    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return UserPublic.model_validate(db_user)


async def update_user_me(
    session: AsyncSession, user_id: int, user_update: UserUpdateMe
) -> UserPublic:
    db_user = await get_user(session, user_id)

    user_data = user_update.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return UserPublic.model_validate(db_user)


async def soft_delete_user(session: AsyncSession, user_id: int) -> UserPublic:
    db_user = await get_user(session, user_id)

    db_user.deleted_at = datetime.now()

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return UserPublic.model_validate(db_user)
