from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select
from sqlalchemy.orm import selectinload

from app.models.evaluation_model import Evaluation, StatusEnum
from app.models.notification_model import (
    Notification,
    NotificationBase,
    NotificationPublic,
)
from app.models.user_model import User
from app.models.user_zone_model import UserZone
from app.utils.exeptions import NotFoundException


async def get_notifications(
    session: AsyncSession,
    company_id: Optional[int] = None,
    role: Optional[int] = None,
    user_id: Optional[int] = None,
) -> List[NotificationPublic]:

    query = (
        select(Notification)
        .options(
            selectinload(Notification.evaluation).selectinload(Evaluation.campaign),
            selectinload(Notification.user),
        )
        .where(Notification.deleted_at == None)
    )

    if company_id is not None:
        query = query.join(User, Notification.user_id == User.id, isouter=True).where(
            User.company_id == company_id
        )

    if role is not None and role in [2]:
        user_zone_ids_subq = (
            select(UserZone.zone_id)
            .where(UserZone.user_id == user_id, UserZone.deleted_at == None)
            .subquery()
        )
        user_ids_subq = (
            select(UserZone.user_id)
            .where(
                UserZone.zone_id.in_(select(user_zone_ids_subq)),
                UserZone.deleted_at == None,
            )
            .subquery()
        )
        query = query.where(
            Notification.status in [StatusEnum.SEND, StatusEnum.UPDATED],
            Notification.user_id.in_(select(user_ids_subq)),
        )

    if role is not None and role == 3:
        query = query.where(
            Notification.status.in_(
                [StatusEnum.APROVED, StatusEnum.EDIT, StatusEnum.REJECTED]
            )
        )

    if user_id is not None:
        query = query.where(Notification.user_id == user_id)

    query = query.order_by(Notification.id)

    result = await session.execute(query)
    db_notifications = result.scalars().all()

    return [NotificationPublic.model_validate(n) for n in db_notifications]


async def get_notification_count(
    session: AsyncSession,
    company_id: Optional[int] = None,
    role: Optional[int] = None,
    user_id: Optional[int] = None,
) -> int:

    query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.read == False, Notification.deleted_at == None)
    )

    if company_id is not None:
        query = query.join(User, Notification.user_id == User.id, isouter=True).where(
            User.company_id == company_id
        )

    if role is not None and role == 2:
        user_zone_ids_subq = (
            select(UserZone.zone_id)
            .where(UserZone.user_id == user_id, UserZone.deleted_at == None)
            .subquery()
        )
        user_ids_subq = (
            select(UserZone.user_id)
            .where(
                UserZone.zone_id.in_(select(user_zone_ids_subq)),
                UserZone.deleted_at == None,
            )
            .subquery()
        )
        query = query.where(
            Notification.status in [StatusEnum.SEND, StatusEnum.UPDATED],
            Notification.user_id.in_(select(user_ids_subq)),
        )

    if role is not None and role == 3:
        query = query.where(
            Notification.status.in_(
                [StatusEnum.APROVED, StatusEnum.EDIT, StatusEnum.REJECTED]
            )
        )

    if user_id is not None:
        query = query.where(Notification.user_id == user_id)

    result = await session.execute(query)
    return result.scalar()


async def get_notification(
    session: AsyncSession, notification_id: int
) -> NotificationPublic:

    query = select(Notification).where(
        Notification.id == notification_id, Notification.deleted_at == None
    )

    result = await session.execute(query)
    db_notification = result.scalars().first()

    if not db_notification:
        raise NotFoundException("Notification not found")

    return db_notification


async def create_notification(
    session: AsyncSession, notification: NotificationBase
) -> NotificationPublic:

    db_notification = Notification(**notification.model_dump(exclude_unset=True))

    session.add(db_notification)
    await session.commit()
    await session.refresh(db_notification)

    return NotificationPublic.model_validate(db_notification)


async def mark_as_read(
    session: AsyncSession, notification_id: int
) -> NotificationPublic:
    db_notification = await get_notification(session, notification_id)

    db_notification.read = True

    session.add(db_notification)
    await session.commit()
    await session.refresh(db_notification)


async def soft_delete_notification(
    session: AsyncSession, notification_id: int
) -> NotificationPublic:
    db_notification = await get_notification(session, notification_id)

    db_notification.deleted_at = datetime.now()

    session.add(db_notification)
    await session.commit()
    await session.refresh(db_notification)

    return db_notification
