from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.campaign_goals_evaluator_model import (
    CampaignGoalsEvaluator,
    CampaignGoalsEvaluatorBase,
    CampaignGoalsEvaluatorPublic,
    CampaignGoalsEvaluatorUpdate,
    CampaignGoalsEvaluatorsPublic,
)
from app.models.campaign_model import Campaign
from app.models.user_model import User
from app.services.campaign_services import get_campaign
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_campaign_goals_evaluator(
    session: AsyncSession,
    offset: int,
    limit: int,
    filter: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[int] = None,
) -> CampaignGoalsEvaluatorsPublic:

    query = (
        select(CampaignGoalsEvaluator, func.count().over().label("total"))
        .join(User, CampaignGoalsEvaluator.evaluator_id == User.id, isouter=True)
        .join(Campaign, CampaignGoalsEvaluator.campaign_id == Campaign.id, isouter=True)
        .options(
            selectinload(CampaignGoalsEvaluator.campaign),
            selectinload(CampaignGoalsEvaluator.evaluator),
        )
        .where(User.company_id == company_id, CampaignGoalsEvaluator.deleted_at == None)
    )

    if filter and search:
        match filter:
            case "evaluator":
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

            case "campaign":
                query = query.where(Campaign.name.ilike(f"%{search}%"))

            case "goal":
                try:
                    goal_int = int(search)
                    query = query.where(CampaignGoalsEvaluator.goal == goal_int)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"La meta del evaluador no es un número",
                    )

    query = query.order_by(CampaignGoalsEvaluator.id).offset(offset).limit(limit)

    result = await session.execute(query)
    db_campaign_goals_evaluators = result.unique().all()

    if not db_campaign_goals_evaluators:
        raise NotFoundException("Campaign goals evaluators not found")

    campaign_goals_evaluators = [
        CampaignGoalsEvaluatorPublic.model_validate(row[0])
        for row in db_campaign_goals_evaluators
    ]
    total = db_campaign_goals_evaluators[0][1] if db_campaign_goals_evaluators else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return CampaignGoalsEvaluatorsPublic(
        data=campaign_goals_evaluators, pagination=pagination
    )


async def get_campaign_goals_evaluator_by_id(
    session: AsyncSession, id: int
) -> CampaignGoalsEvaluatorPublic:
    query = (
        select(CampaignGoalsEvaluator)
        .where(
            CampaignGoalsEvaluator.id == id,
            CampaignGoalsEvaluator.deleted_at == None,
        )
        .options(
            selectinload(CampaignGoalsEvaluator.evaluator),
            selectinload(CampaignGoalsEvaluator.campaign),
        )
    )

    result = await session.execute(query)
    db_campaign_goals_evaluator = result.scalars().first()

    if not db_campaign_goals_evaluator:
        raise NotFoundException("Campaign goals evaluator not found")

    return db_campaign_goals_evaluator


async def create_campaign_goals_evaluator(
    session: AsyncSession, campaign_goals_evaluator: CampaignGoalsEvaluatorBase
) -> CampaignGoalsEvaluatorPublic:

    # obtener campaña
    campaign = await get_campaign(session, campaign_goals_evaluator.campaign_id)

    current_total = await calculate_total_assigned_goal(
        session, campaign_goals_evaluator.campaign_id
    )

    # Verificar si la nueva meta excede la meta máxima
    if current_total + campaign_goals_evaluator.goal > campaign.goal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La meta del evaluador supera la meta máxima de la campaña",
        )

    # Crear meta para evaluador
    db_campaign_goals_evaluator = CampaignGoalsEvaluator(
        **campaign_goals_evaluator.model_dump()
    )

    session.add(db_campaign_goals_evaluator)
    await session.commit()
    await session.refresh(db_campaign_goals_evaluator)

    return CampaignGoalsEvaluatorPublic.model_validate(db_campaign_goals_evaluator)


async def update_campaign_goals_evaluator(
    session: AsyncSession,
    campaign_goals_evaluator_id: int,
    campaign_goals_evaluator: CampaignGoalsEvaluatorUpdate,
) -> CampaignGoalsEvaluatorPublic:
    # Obtener instancia actual
    db_campaign_goals_evaluator = await get_campaign_goals_evaluator_by_id(
        session, campaign_goals_evaluator_id
    )

    # Verificar si se está actualizando el campo 'goal'
    updated_data = campaign_goals_evaluator.model_dump(exclude_unset=True)
    new_goal = updated_data.get("goal")

    if new_goal is not None:
        # Obtener campaña asociada
        campaign = await get_campaign(session, db_campaign_goals_evaluator.campaign_id)

        # Calcular total actual sin contar el evaluador editado
        current_total = await calculate_total_assigned_goal(
            session,
            db_campaign_goals_evaluator.campaign_id,
            exclude_evaluator_id=campaign_goals_evaluator_id,
        )

        # Verificar si la nueva suma excede la meta máxima
        if current_total + new_goal > campaign.goal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La meta actualizada del evaluador supera la meta máxima de la campaña",
            )

    # Aplicar actualización
    db_campaign_goals_evaluator.sqlmodel_update(updated_data)

    session.add(db_campaign_goals_evaluator)
    await session.commit()
    await session.refresh(db_campaign_goals_evaluator)

    return CampaignGoalsEvaluatorPublic.model_validate(db_campaign_goals_evaluator)


async def soft_delete_campaign_goals_evaluator(
    session: AsyncSession, campaign_goals_evaluator_id: int
) -> CampaignGoalsEvaluatorPublic:
    db_campaign_goals_evaluator = await get_campaign_goals_evaluator_by_id(
        session, campaign_goals_evaluator_id
    )

    db_campaign_goals_evaluator.deleted_at = datetime.now()

    session.add(db_campaign_goals_evaluator)
    await session.commit()
    await session.refresh(db_campaign_goals_evaluator)

    return db_campaign_goals_evaluator


async def calculate_total_assigned_goal(
    session: AsyncSession,
    campaign_id: int,
    exclude_evaluator_id: Optional[int] = None,
) -> int:
    query = select(func.coalesce(func.sum(CampaignGoalsEvaluator.goal), 0)).where(
        CampaignGoalsEvaluator.campaign_id == campaign_id
    )
    if exclude_evaluator_id is not None:
        query = query.where(CampaignGoalsEvaluator.id != exclude_evaluator_id)

    result = await session.execute(query)
    return result.scalar_one()
