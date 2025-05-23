from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.user_zone_model import (
    AssignZonesRequest,
    UserZonePublic,
    UserZonesPublic,
)
from app.services.user_zone_services import (
    create_zone_users,
    get_user_zone,
    get_users_zones,
    soft_delete_user_zone,
    update_user_zone,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/user-zone",
    tags=["User Zone"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request,
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    filter: Optional[str] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> UserZonesPublic:

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve all users zones")

    if request.state.user.role in [1, 2]:
        user_zones = await get_users_zones(
            session,
            offset,
            limit,
            filter,
            search,
            request.state.user.company_id,
        )
    else:
        user_zones = await get_users_zones(session, offset, limit, filter, search)

    return user_zones


@router.get("/{user_zone_id}")
async def get_one(
    request: Request,
    user_zone_id: int,
    session: AsyncSession = Depends(get_db),
) -> UserZonePublic:

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve this user zone")

    user_zone = await get_user_zone(session, user_zone_id)

    if request.state.user.role in [1, 2]:
        if user_zone.user.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="retrieve this user zone")

    return user_zone


@router.post("/")
async def create(
    request: Request,
    data: AssignZonesRequest,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="create a user zone")

    save_user_zones = await create_zone_users(session, data)

    return save_user_zones


@router.put("/{user_zone_id}")
async def update(
    request: Request,
    user_zone_id: int,
    new_zone_id: int,
    session: AsyncSession = Depends(get_db),
) -> UserZonePublic:

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="update this user zone")

    user_zone = await update_user_zone(session, user_zone_id, new_zone_id)

    return user_zone


@router.delete("/{user_zone_id}")
async def delete(
    request: Request,
    user_zone_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="delete this user zone")

    await soft_delete_user_zone(session, user_zone_id)

    return {"message": "User zone deleted"}
