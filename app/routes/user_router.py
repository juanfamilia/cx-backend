from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user_model import (
    UserCreate,
    UserPublic,
    UserUpdate,
    UserUpdateMe,
    UsersPublic,
)
from app.services.users_services import (
    create_user,
    get_user,
    get_user_by_zone,
    get_users,
    soft_delete_user,
    update_user,
    update_user_me,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException
from app.utils.helpers.role_checker import check_role_creation_permissions

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> UsersPublic:

    role = request.state.user.role

    if role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve all users")

    match role:
        case 0:
            return await get_users(session, offset, limit, filter, search)

        case 1:
            return await get_users(
                session, offset, limit, filter, search, request.state.user.company_id
            )

        case 2:
            return await get_user_by_zone(
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.id,
                request.state.user.company_id,
            )


@router.get("/me")
async def get_current(request: Request) -> UserPublic:

    if not request.state.user:
        raise JSONResponse(
            content="User session not found or expired session",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return request.state.user


@router.put("/me/{user_id}")
async def update_current(
    request: Request,
    user_update: UserUpdateMe,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    user = await update_user_me(session, request.state.user.id, user_update)

    return user


@router.get("/{user_id}")
async def get_one(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    user = await get_user(session, user_id)

    if request.state.user.role not in [0, 1]:
        if user.id != request.state.user.id:
            raise PermissionDeniedException(custom_message="retrieve this user")

    if (
        request.state.user.role == 1
        and user.company_id != request.state.user.company_id
    ):
        raise PermissionDeniedException(custom_message="retrieve this user")

    return user


@router.post("/", response_model=UserPublic)
async def create(
    request: Request, user_create: UserCreate, session: AsyncSession = Depends(get_db)
) -> UserPublic:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create users")

    if request.state.user.role == 1:
        user_create.company_id = request.state.user.company_id

    check_role_creation_permissions(request.state.user.role, user_create.role)

    save_user = await create_user(session, user_create)

    return save_user


@router.put("/{user_id}", response_model=UserPublic)
async def update_any(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="update this user")

    if (
        request.state.user.role == 1
        and request.state.user.company != user_update.company_id
    ):
        raise PermissionDeniedException(custom_message="update this user")

    check_role_creation_permissions(request.state.user.role, user_update.role)

    updated_user = await update_user(session, user_id, user_update)

    return updated_user


@router.delete("/{user_id}")
async def delete(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
):

    user = await get_user(session, user_id)

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="delete this user")

    if request.state.user.role == 1 and request.state.user.company != user.company_id:
        raise PermissionDeniedException(custom_message="delete this user")

    await soft_delete_user(session, user_id)

    return {"message": "User deleted"}
