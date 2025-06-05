from typing import List, Optional
from fastapi import Query
from sqlmodel import and_, func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.security import get_password_hash
from app.models.company_model import Company
from app.models.user_model import (
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserUpdateMe,
    UsersPublic,
)
from app.models.user_zone_model import UserZone
from app.types.pagination import Pagination
from app.utils.exeptions import InvalidCredentialsException, NotFoundException


async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: int | None = None,
) -> UsersPublic:

    query = (
        select(User, func.count().over().label("total"))
        .options(selectinload(User.company))
        .where(User.deleted_at == None)
    )

    if company_id is not None:
        query = query.where(User.company_id == company_id)

    if filter and search:
        match filter:
            case "full_name":
                names = search.split()
                if len(names) == 1:
                    query = query.where(
                        or_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{names[0]}%"),
                        )
                    )
                else:
                    query = query.where(
                        and_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{' '.join(names[1:])}%"),
                        )
                    )

            case "email":
                query = query.where(User.email.ilike(f"%{search}%"))

            case "company":
                query = query.where(Company.name.ilike(f"%{search}%"))

    query = query.order_by(User.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_users = result.unique().all()

    if not db_users:
        raise NotFoundException("Users not found")

    patients = [row[0] for row in db_users]
    total = db_users[0][1] if db_users else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return UsersPublic(data=patients, pagination=pagination)


async def get_users_plain(
    session: AsyncSession,
    company_id: int | None = None,
    user_id: int | None = None,
):

    query = (
        select(User)
        .options(selectinload(User.company))
        .join(UserZone, User.id == UserZone.user_id)
        .where(User.role == 3, User.deleted_at == None)
    )

    if company_id is not None:
        query = query.where(User.company_id == company_id)

    if user_id is not None:
        # Obtener las zonas del usuario que hace la consulta
        user_zones = await session.execute(
            select(UserZone.zone_id).where(
                UserZone.user_id == user_id, UserZone.deleted_at == None
            )
        )
        zone_ids = [row[0] for row in user_zones]

        if not zone_ids:
            raise NotFoundException("No zones assigned to user")

        # Filtrar usuarios por las zonas del usuario que consulta
        query = query.where(UserZone.zone_id.in_(zone_ids))

    query = query.order_by(User.id)

    result = await session.execute(query)
    db_users = result.scalars().unique().all()

    if not db_users:
        raise NotFoundException("Users not found")

    users = [
        {"name": f"{user.first_name} {user.last_name}", "value": user.id}
        for user in db_users
    ]

    return users


async def get_user(session: AsyncSession, user_id: int) -> UserPublic:

    db_user = await session.get(User, user_id)

    if not db_user:
        raise NotFoundException("User not found")

    return db_user


async def get_user_by_zone(
    session: AsyncSession,
    offset: int,
    limit: int,
    filter: Optional[str],
    search: Optional[str],
    user_id: int,
    company_id: int,
) -> UsersPublic:
    # Obtener zonas del usuario autenticado
    user_zone_ids_subq = (
        select(UserZone.zone_id)
        .where(UserZone.user_id == user_id, UserZone.deleted_at == None)
        .subquery()
    )

    # Usuarios que comparten zonas con el actual
    user_ids_subq = (
        select(UserZone.user_id)
        .where(
            UserZone.zone_id.in_(select(user_zone_ids_subq)),
            UserZone.deleted_at == None,
        )
        .subquery()
    )

    # Construcción del query principal
    query = (
        select(User, func.count().over().label("total"))
        .join(Company, User.company_id == Company.id, isouter=True)
        .where(
            User.deleted_at == None,
            User.id.in_(select(user_ids_subq)),
            User.company_id == company_id,
            User.id != user_id,  # 👈 EXCLUYE al usuario autenticado
        )
        .options(selectinload(User.company))
    )

    # Filtros
    if filter and search:
        match filter:
            case "full_name":
                names = search.split()
                if len(names) == 1:
                    query = query.where(
                        or_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{names[0]}%"),
                        )
                    )
                else:
                    query = query.where(
                        and_(
                            User.first_name.ilike(f"%{names[0]}%"),
                            User.last_name.ilike(f"%{' '.join(names[1:])}%"),
                        )
                    )

            case "email":
                query = query.where(User.email.ilike(f"%{search}%"))

            case "company":
                query = query.where(Company.name.ilike(f"%{search}%"))

    # Paginación
    query = query.order_by(User.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_users = result.unique().all()

    if not db_users:
        raise NotFoundException("Users not found")

    users = [row[0] for row in db_users]
    total = db_users[0][1] if db_users else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return UsersPublic(data=users, pagination=pagination)


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User:

    query = select(User).where(User.email == email)

    result = await session.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise InvalidCredentialsException()

    return User.model_validate(db_user)


async def create_user(session: AsyncSession, user: UserCreate) -> UserPublic:
    hashed_password = get_password_hash(user.password)

    db_user = User(
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        email=user.email,
        company_id=user.company_id,
        hashed_password=hashed_password,
    )

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


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
