from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.action_plan_model import (
    ActionPlanCreate,
    ActionPlanPublic,
    ActionPlanStatus,
    ActionPlanUpdate,
    ActionPlansPublic,
)
from app.services.action_plan_services import (
    create_action_plan,
    get_action_plan,
    get_action_plans,
    update_action_plan,
)
from app.services.audit_services import log_change
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/action-plans",
    tags=["Action Plans"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/", response_model=ActionPlansPublic)
async def list_plans(
    request: Request,
    session: AsyncSession = Depends(get_db),
    evaluation_id: Optional[int] = Query(None),
    assigned_to: Optional[int] = Query(None),
    status: Optional[ActionPlanStatus] = Query(None),
    overdue_only: bool = Query(False),
    offset: int = 0,
    limit: int = Query(default=50, le=200),
) -> ActionPlansPublic:
    user = request.state.user
    if user.role == 3:
        raise PermissionDeniedException(custom_message="access action plans")
    return await get_action_plans(
        session,
        company_id=user.company_id,
        evaluation_id=evaluation_id,
        assigned_to=assigned_to,
        status=status,
        overdue_only=overdue_only,
        offset=offset,
        limit=limit,
    )


@router.get("/{plan_id}", response_model=ActionPlanPublic)
async def get_one(
    request: Request,
    plan_id: int,
    session: AsyncSession = Depends(get_db),
) -> ActionPlanPublic:
    user = request.state.user
    plan = await get_action_plan(session, plan_id)
    if user.role != 0 and plan.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="access this action plan")
    return plan


@router.post("/", response_model=ActionPlanPublic, status_code=201)
async def create(
    request: Request,
    payload: ActionPlanCreate,
    session: AsyncSession = Depends(get_db),
) -> ActionPlanPublic:
    user = request.state.user
    if user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="create action plans")
    plan = await create_action_plan(
        session, payload,
        company_id=user.company_id,
        created_by=user.id,
    )
    await log_change(
        session,
        user_id=user.id,
        user_email=user.email,
        entity_type="action_plans",
        entity_id=plan.id,
        action="create",
        new_value=payload.title,
    )
    return plan


@router.put("/{plan_id}", response_model=ActionPlanPublic)
async def update(
    request: Request,
    plan_id: int,
    payload: ActionPlanUpdate,
    session: AsyncSession = Depends(get_db),
) -> ActionPlanPublic:
    user = request.state.user
    if user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="update action plans")

    plan = await get_action_plan(session, plan_id)
    if user.role != 0 and plan.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="update this action plan")

    prev_status = plan.status
    updated = await update_action_plan(session, plan_id, payload)

    if payload.status and payload.status != prev_status:
        await log_change(
            session,
            user_id=user.id,
            user_email=user.email,
            entity_type="action_plans",
            entity_id=plan_id,
            action="status_change",
            field_name="status",
            old_value=prev_status,
            new_value=payload.status,
            justification=payload.resolution_notes,
        )
    return updated
