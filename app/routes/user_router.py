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
    get_users,
    get_users_plain,
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
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.company_id,
                request.state.user.id,
            )

        case 2:
            # Misma amplitud que admin empresa: todos los usuarios activos de la compañía
            # (get_user_by_zone ocultaba evaluadores sin filas en user_zones).
            return await get_users(
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.company_id,
                request.state.user.id,
            )


@router.get("/plain-list")
async def get_users_plain_list(
    request: Request, session: AsyncSession = Depends(get_db)
):
    role = request.state.user.role

    if role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve all users")

    match role:
        case 0:
            return await get_users_plain(session)

        case 1:
            return await get_users_plain(session, request.state.user.company_id)

        case 2:
            return await get_users_plain(session, request.state.user.company_id)


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
    actor = request.state.user

    if actor.role in (0, 1):
        if actor.role == 1 and user.company_id != actor.company_id:
            raise PermissionDeniedException(custom_message="retrieve this user")
        return user

    if actor.role == 2:
        if user.id == actor.id:
            return user
        if (
            user.role == 3
            and user.company_id is not None
            and user.company_id == actor.company_id
        ):
            return user
        raise PermissionDeniedException(custom_message="retrieve this user")

    if user.id != actor.id:
        raise PermissionDeniedException(custom_message="retrieve this user")

    return user


@router.post("/", response_model=UserPublic)
async def create(
    request: Request, user_create: UserCreate, session: AsyncSession = Depends(get_db)
) -> UserPublic:

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="create users")

    update_payload: dict = {}
    if request.state.user.role in [1, 2]:
        cid = request.state.user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="crear usuarios (sin empresa asignada en tu cuenta)"
            )
        update_payload["company_id"] = cid

    if user_create.birthdate is not None:
        update_payload["birthdate"] = user_create.birthdate.replace(tzinfo=None)

    if update_payload:
        user_create = user_create.model_copy(update=update_payload)

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

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="update this user")

    actor = request.state.user
    target = await get_user(session, user_id)

    if actor.role == 2:
        if actor.company_id is None:
            raise PermissionDeniedException(
                custom_message="actualizar usuarios (sin empresa asignada en tu cuenta)"
            )
        if target.company_id != actor.company_id or target.role != 3:
            raise PermissionDeniedException(custom_message="update this user")
        payload = user_update.model_dump(exclude_unset=True)
        new_role = payload.get("role", target.role)
        if new_role != 3:
            raise PermissionDeniedException(
                custom_message="solo puedes mantener el rol de evaluador en este usuario"
            )
        user_update = user_update.model_copy(update={"company_id": actor.company_id})
        check_role_creation_permissions(actor.role, new_role)
    else:
        if (
            actor.role == 1
            and user_update.company_id is not None
            and actor.company_id != user_update.company_id
        ):
            raise PermissionDeniedException(custom_message="update users to other company")

        check_role_creation_permissions(actor.role, user_update.role)

    if user_update.birthdate:
        user_update.birthdate = user_update.birthdate.replace(tzinfo=None)

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

    if request.state.user.role == 1 and request.state.user.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="delete this user")

    await soft_delete_user(session, user_id)

    return {"message": "User deleted"}
