from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.notification_model import NotificationPublic
from app.services.notification_services import (
    get_notification_count,
    get_notifications,
    mark_as_read,
    soft_delete_notification,
)
from app.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/notification",
    tags=["Notification"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request, session: AsyncSession = Depends(get_db)
) -> List[NotificationPublic]:

    match request.state.user.role:
        case 0:
            notifications = await get_notifications(session)

        case 1:
            notifications = await get_notifications(
                session, request.state.user.company_id
            )

        case 2:
            notifications = await get_notifications(
                session,
                request.state.user.company_id,
                request.state.user.role,
                request.state.user.id,
            )
        case 3:
            notifications = await get_notifications(
                session,
                request.state.user.company_id,
                request.state.user.role,
                request.state.user.id,
            )

    return notifications


@router.get("/count")
async def get_count(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> int:

    match request.state.user.role:
        case 0:
            count = await get_notification_count(session)

        case 1:
            count = await get_notification_count(session, request.state.user.company_id)

        case 2:
            count = await get_notification_count(
                session,
                request.state.user.company_id,
                request.state.user.role,
                request.state.user.id,
            )
        case 3:
            count = await get_notification_count(
                session,
                request.state.user.company_id,
                request.state.user.role,
                request.state.user.id,
            )

    return count


@router.get("/mark-as-read/{notification_id}")
async def mark(
    request: Request,
    notification_id: int,
    session: AsyncSession = Depends(get_db),
) -> NotificationPublic:
    notification = await mark_as_read(session, notification_id)

    return notification


@router.delete("/{notification_id}")
async def delete(
    notification_id: int,
    session: AsyncSession = Depends(get_db),
):
    await soft_delete_notification(session, notification_id)

    return {"message": "Notification deleted"}
