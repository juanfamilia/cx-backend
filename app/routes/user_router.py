from fastapi import APIRouter, Depends, Request, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.users_model import UserCreate, UserPublic, UserUpdate, UserUpdateMe
from app.services.users_services import (
    create_user,
    get_user,
    get_users,
    soft_delete_user,
    update_user,
    update_user_me,
)
from app.utils.deps import get_auth_user
from app.utils.exeptions import PermissionDeniedException

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_auth_user)],
)


@router.get("/")
async def get_all_users(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=100),
) -> list[UserPublic]:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="retrieve all users")

    users = await get_users(session, offset, limit)

    return users


@router.get("/me")
async def get_current_user(request: Request) -> UserPublic:

    if not request.state.user:
        raise JSONResponse(
            content="User session not found or expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return request.state.user


@router.put("/me/{user_id}")
async def update_current_user(
    request: Request,
    user_update: UserUpdateMe,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    user = await update_user_me(session, request.state.user.id, user_update)

    return user


@router.get("/{user_id}")
async def get_one_user(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    user = await get_user(session, user_id)

    if request.state.user.role not in [0, 1]:
        if user.id != request.state.user.id:
            raise PermissionDeniedException(custom_message="retrieve this user")

    return user


@router.post("/", response_model=UserCreate)
async def register_user(
    request: Request, user_create: UserCreate, session: AsyncSession = Depends(get_db)
) -> UserPublic:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create users")

    save_user = await create_user(session, user_create)

    return save_user


@router.put("/{user_id}", response_model=UserPublic)
async def update_any_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
) -> UserPublic:

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="update this user")

    updated_user = await update_user(session, user_id, user_update)

    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="delete this user")

    await soft_delete_user(session, user_id)

    return {"message": "User deleted"}
