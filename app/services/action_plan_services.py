"""
Action Plan Services — Workflow de Corrección

Ciclo completo:
  Evaluación rechazada → auto-generación de plan → asignación a gerente
  → seguimiento → resolución → re-evaluación opcional
"""

import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.action_plan_model import (
    ActionPlan,
    ActionPlanCreate,
    ActionPlanPriority,
    ActionPlanPublic,
    ActionPlanStatus,
    ActionPlanUpdate,
    ActionPlansPublic,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def create_action_plan(
    session: AsyncSession,
    payload: ActionPlanCreate,
    company_id: int,
    created_by: int,
) -> ActionPlan:
    plan = ActionPlan(
        **payload.model_dump(),
        company_id=company_id,
        created_by_user_id=created_by,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def get_action_plan(session: AsyncSession, plan_id: int) -> ActionPlan:
    plan = await session.get(ActionPlan, plan_id)
    if not plan or plan.deleted_at is not None:
        raise NotFoundException("Action plan not found")
    return plan


async def update_action_plan(
    session: AsyncSession, plan_id: int, payload: ActionPlanUpdate
) -> ActionPlan:
    plan = await get_action_plan(session, plan_id)
    data = payload.model_dump(exclude_unset=True)

    if "status" in data and data["status"] == ActionPlanStatus.RESOLVED:
        data["resolved_at"] = datetime.now(timezone.utc)

    for key, value in data.items():
        setattr(plan, key, value)

    # Auto-marcar como OVERDUE si se actualiza después del vencimiento sin resolver
    if (
        plan.due_date
        and plan.status not in (ActionPlanStatus.RESOLVED, ActionPlanStatus.CANCELLED)
        and plan.due_date < date.today()
    ):
        plan.status = ActionPlanStatus.OVERDUE

    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def get_action_plans(
    session: AsyncSession,
    company_id: int,
    evaluation_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[ActionPlanStatus] = None,
    overdue_only: bool = False,
    offset: int = 0,
    limit: int = 50,
) -> ActionPlansPublic:
    conditions = [
        ActionPlan.company_id == company_id,
        ActionPlan.deleted_at.is_(None),
    ]
    if evaluation_id is not None:
        conditions.append(ActionPlan.evaluation_id == evaluation_id)
    if assigned_to is not None:
        conditions.append(ActionPlan.assigned_to_user_id == assigned_to)
    if status is not None:
        conditions.append(ActionPlan.status == status)
    if overdue_only:
        conditions.append(ActionPlan.due_date < date.today())
        conditions.append(ActionPlan.status == ActionPlanStatus.PENDING)

    count_q = select(func.count(ActionPlan.id)).where(*conditions)
    total = (await session.execute(count_q)).scalar_one()

    q = (
        select(ActionPlan)
        .where(*conditions)
        .order_by(ActionPlan.due_date.asc().nullslast(), ActionPlan.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(q)).scalars().all()

    return ActionPlansPublic(
        data=[ActionPlanPublic.model_validate(r) for r in rows],
        pagination=Pagination(first=offset, rows=limit, total=total),
    )


# ---------------------------------------------------------------------------
# Auto-generación desde pipeline de IA
# ---------------------------------------------------------------------------

_IRD_THRESHOLD = 70   # Si IRD > 70, generar plan crítico
_IOC_THRESHOLD = 40   # Si IOC < 40, generar plan de oportunidad
_CES_THRESHOLD = 60   # Si CES > 60, generar plan de proceso


def _auto_plans_from_operative(
    evaluation_id: int,
    company_id: int,
    operative_view: str,
) -> List[ActionPlanCreate]:
    """
    Analiza el JSON operativo y genera planes de acción automáticos
    basados en las reglas de negocio del programa.
    """
    plans: List[ActionPlanCreate] = []

    try:
        match = re.search(r"```json\s*(.*?)\s*```", operative_view, re.DOTALL)
        json_str = match.group(1) if match else operative_view
        data = json.loads(json_str)
    except Exception:
        return plans

    ird = (data.get("IRD") or {}).get("score", 0) or 0
    ioc = (data.get("IOC") or {}).get("score", 100) or 100
    ces = (data.get("CES") or {}).get("score", 0) or 0
    acciones = data.get("acciones_sugeridas") or []

    if ird > _IRD_THRESHOLD:
        plans.append(ActionPlanCreate(
            evaluation_id=evaluation_id,
            title="Riesgo de deserción detectado — Intervención urgente",
            description=(
                f"El índice de riesgo de deserción (IRD={ird}) supera el umbral crítico ({_IRD_THRESHOLD}). "
                f"Justificación IA: {(data.get('IRD') or {}).get('justificacion', '')}. "
                "Se requiere revisión del protocolo de cortesía y atención en esta sucursal."
            ),
            priority=ActionPlanPriority.CRITICAL,
            due_date=date.today() + timedelta(days=5),
            requires_reevaluation=True,
            reevaluation_due_date=date.today() + timedelta(days=30),
            source="ai_auto",
        ))

    if ioc < _IOC_THRESHOLD:
        plans.append(ActionPlanCreate(
            evaluation_id=evaluation_id,
            title="Baja captación comercial — Plan de capacitación",
            description=(
                f"El índice de oportunidad comercial (IOC={ioc}) está por debajo del mínimo ({_IOC_THRESHOLD}). "
                "El colaborador no identificó o no gestionó la oportunidad de venta/servicio. "
                "Se recomienda capacitación en prospección de productos."
            ),
            priority=ActionPlanPriority.HIGH,
            due_date=date.today() + timedelta(days=14),
            source="ai_auto",
        ))

    if ces > _CES_THRESHOLD:
        plans.append(ActionPlanCreate(
            evaluation_id=evaluation_id,
            title="Alto esfuerzo del cliente — Simplificación de procesos",
            description=(
                f"El Customer Effort Score (CES={ces}) supera el umbral ({_CES_THRESHOLD}). "
                f"Justificación IA: {(data.get('CES') or {}).get('justificacion', '')}. "
                "Se recomienda revisar los procesos de entrega de información."
            ),
            priority=ActionPlanPriority.MEDIUM,
            due_date=date.today() + timedelta(days=21),
            source="ai_auto",
        ))

    # Acciones sugeridas por la IA que no corresponden a las reglas anteriores
    for accion in acciones:
        if isinstance(accion, str) and len(accion) > 10:
            plans.append(ActionPlanCreate(
                evaluation_id=evaluation_id,
                title=f"Acción IA: {accion[:80]}",
                description=accion,
                priority=ActionPlanPriority.LOW,
                due_date=date.today() + timedelta(days=30),
                source="ai_auto",
            ))

    return plans


async def auto_generate_action_plans(
    session: AsyncSession,
    evaluation_id: int,
    company_id: int,
    operative_view: str,
    system_user_id: int = 1,
) -> List[ActionPlan]:
    """
    Genera y persiste automáticamente los planes de acción al finalizar el pipeline de IA.
    Idempotente: no duplica planes si ya existen planes ai_auto para esta evaluación.
    """
    existing_q = select(func.count(ActionPlan.id)).where(
        ActionPlan.evaluation_id == evaluation_id,
        ActionPlan.source == "ai_auto",
        ActionPlan.deleted_at.is_(None),
    )
    existing_count = (await session.execute(existing_q)).scalar_one()
    if existing_count > 0:
        logger.info("Auto plans already exist evaluation_id=%s, skipping", evaluation_id)
        return []

    plan_templates = _auto_plans_from_operative(evaluation_id, company_id, operative_view)
    saved = []
    for template in plan_templates:
        plan = ActionPlan(
            **template.model_dump(),
            company_id=company_id,
            created_by_user_id=system_user_id,
        )
        session.add(plan)
        saved.append(plan)

    if saved:
        await session.commit()
        for p in saved:
            await session.refresh(p)
        logger.info(
            "Auto-generated %s action plans for evaluation_id=%s",
            len(saved), evaluation_id
        )
    return saved
