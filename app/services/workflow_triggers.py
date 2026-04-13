"""
Workflow Triggers — Post-transition logic for evaluation status changes.

Called by change_evaluation_status in evaluation_services.py after a
status transition is persisted.  Every function runs as a FastAPI
BackgroundTask (fire-and-forget) so it never blocks the HTTP response.

Flow summary
────────────
  ENVIADO → EDITAR     → email evaluador (con comentario del revisor)
  EDITAR  → ACTUALIZADO → email revisores de la empresa
  *       → APROBADO   → email evaluador + auto-generar planes de acción por NCs
  *       → RECHAZADO  → email evaluador + plan de revisita si procede
"""

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.action_plan_model import ActionPlan, ActionPlanCreate, ActionPlanPriority
from app.models.evaluation_model import Evaluation, EvaluationAnswer, RejectionTypeEnum, StatusEnum
from app.models.survey_model import SurveyAspect
from app.models.user_model import User
from app.services.email_service import (
    email_evaluation_approved,
    email_evaluation_rejected,
    email_evaluation_sent_to_edit,
    email_evaluation_ready_for_review,
    send_email,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def fire_workflow_trigger(
    session: AsyncSession,
    evaluation_id: int,
    new_status: StatusEnum,
    old_status: StatusEnum,
    actor_user_id: int,
    comment: Optional[str] = None,
    rejection_type: Optional[str] = None,
    requires_revisit: bool = False,
) -> None:
    """Dispatch the correct trigger based on the new status."""
    try:
        evaluation = await _load_evaluation(session, evaluation_id)
        if evaluation is None:
            logger.warning("workflow_trigger: evaluation %s not found", evaluation_id)
            return

        actor = await session.get(User, actor_user_id)
        actor_name = f"{actor.first_name} {actor.last_name}".strip() if actor else "Sistema"

        match new_status:
            case StatusEnum.APROVED:
                await _on_approved(session, evaluation, actor_name, comment)
            case StatusEnum.REJECTED:
                await _on_rejected(session, evaluation, actor_name, comment, rejection_type, requires_revisit)
            case StatusEnum.EDIT:
                await _on_edit(session, evaluation, actor_name, comment)
            case StatusEnum.UPDATED:
                await _on_updated(session, evaluation)
            case _:
                pass
    except Exception as exc:
        logger.error("workflow_trigger error [eval=%s status=%s]: %s", evaluation_id, new_status, exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_evaluation(session: AsyncSession, evaluation_id: int) -> Optional[Evaluation]:
    result = await session.execute(
        select(Evaluation)
        .where(Evaluation.id == evaluation_id)
        .options(
            selectinload(Evaluation.user),
            selectinload(Evaluation.campaign),
            selectinload(Evaluation.evaluation_answers),
        )
    )
    return result.scalars().first()


async def _get_company_reviewers(session: AsyncSession, company_id: int) -> list[User]:
    """Return Admin (role=1) and Gerente (role=2) users of the same company."""
    result = await session.execute(
        select(User).where(
            User.company_id == company_id,
            User.role.in_([1, 2]),
            User.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Trigger: APROBADO
# ---------------------------------------------------------------------------

async def _on_approved(
    session: AsyncSession,
    evaluation: Evaluation,
    actor_name: str,
    comment: Optional[str],
) -> None:
    evaluator = evaluation.user
    campaign_name = evaluation.campaign.name if evaluation.campaign else f"#{evaluation.campaigns_id}"

    # 1) Email al evaluador
    if evaluator and evaluator.email:
        evaluator_name = f"{evaluator.first_name} {evaluator.last_name}".strip()
        subject, html = email_evaluation_approved(
            evaluator_name=evaluator_name,
            evaluation_id=evaluation.id,
            campaign_name=campaign_name,
            reviewer_name=actor_name,
            comment=comment,
        )
        await send_email([evaluator.email], subject, html)

    # 2) Auto-generar planes de acción por NCs
    company_id = evaluation.campaign.company_id if evaluation.campaign else None
    if company_id:
        await _auto_plans_from_nc_answers(session, evaluation, company_id)


async def _auto_plans_from_nc_answers(
    session: AsyncSession,
    evaluation: Evaluation,
    company_id: int,
) -> None:
    """
    Generate one action plan per NC (value_boolean=False) answer.
    Idempotent: skips if plans with source='approval_nc' already exist.
    """
    from sqlmodel import func as sqlfunc

    existing_q = select(sqlfunc.count(ActionPlan.id)).where(
        ActionPlan.evaluation_id == evaluation.id,
        ActionPlan.source == "approval_nc",
        ActionPlan.deleted_at.is_(None),
    )
    existing_count = (await session.execute(existing_q)).scalar_one()
    if existing_count > 0:
        return

    nc_answers = [
        a for a in (evaluation.evaluation_answers or [])
        if a.value_boolean is False
    ]
    if not nc_answers:
        return

    # Load aspect descriptions in one query
    aspect_ids = [a.aspect_id for a in nc_answers if a.aspect_id]
    if not aspect_ids:
        return

    aspects_result = await session.execute(
        select(SurveyAspect).where(SurveyAspect.id.in_(aspect_ids))
    )
    aspects_by_id = {a.id: a for a in aspects_result.scalars().all()}

    plans_created = 0
    due = date.today() + timedelta(days=14)

    for answer in nc_answers:
        aspect = aspects_by_id.get(answer.aspect_id)
        description = aspect.description if aspect else f"Aspecto #{answer.aspect_id}"

        plan = ActionPlan(
            evaluation_id=evaluation.id,
            company_id=company_id,
            title=f"NC: {description[:100]}",
            description=(
                f"No conformidad detectada en la evaluación #{evaluation.id}.\n"
                f"Aspecto: {description}\n"
                f"{f'Observación del evaluador: {answer.comment}' if answer.comment else ''}"
            ).strip(),
            priority=ActionPlanPriority.MEDIUM,
            due_date=due,
            source="approval_nc",
        )
        session.add(plan)
        plans_created += 1

    if plans_created:
        await session.commit()
        logger.info("Auto-generated %s NC action plans for evaluation %s", plans_created, evaluation.id)


# ---------------------------------------------------------------------------
# Trigger: RECHAZADO
# ---------------------------------------------------------------------------

async def _on_rejected(
    session: AsyncSession,
    evaluation: Evaluation,
    actor_name: str,
    comment: Optional[str],
    rejection_type: Optional[str],
    requires_revisit: bool,
) -> None:
    evaluator = evaluation.user
    campaign_name = evaluation.campaign.name if evaluation.campaign else f"#{evaluation.campaigns_id}"
    rtype = rejection_type or RejectionTypeEnum.DISCARDED.value

    # 1) Email al evaluador
    if evaluator and evaluator.email:
        evaluator_name = f"{evaluator.first_name} {evaluator.last_name}".strip()
        subject, html = email_evaluation_rejected(
            evaluator_name=evaluator_name,
            evaluation_id=evaluation.id,
            campaign_name=campaign_name,
            reviewer_name=actor_name,
            rejection_type=rtype,
            requires_revisit=requires_revisit,
            comment=comment,
        )
        await send_email([evaluator.email], subject, html)

    # 2) Si discrepancia + revisita: crear plan de re-visita
    if rtype == RejectionTypeEnum.DISCREPANCY.value and requires_revisit:
        company_id = evaluation.campaign.company_id if evaluation.campaign else None
        if company_id:
            plan = ActionPlan(
                evaluation_id=evaluation.id,
                company_id=company_id,
                title="Re-visita requerida por discrepancia",
                description=(
                    f"La evaluación #{evaluation.id} fue rechazada por discrepancia "
                    f"y requiere una nueva visita a la sucursal."
                    f"{f' Motivo: {comment}' if comment else ''}"
                ),
                priority=ActionPlanPriority.HIGH,
                due_date=date.today() + timedelta(days=7),
                requires_reevaluation=True,
                reevaluation_due_date=date.today() + timedelta(days=21),
                source="rejection_revisit",
            )
            session.add(plan)
            await session.commit()
            logger.info("Created revisit action plan for evaluation %s", evaluation.id)


# ---------------------------------------------------------------------------
# Trigger: EDITAR (devuelto al evaluador)
# ---------------------------------------------------------------------------

async def _on_edit(
    session: AsyncSession,
    evaluation: Evaluation,
    actor_name: str,
    comment: Optional[str],
) -> None:
    evaluator = evaluation.user
    campaign_name = evaluation.campaign.name if evaluation.campaign else f"#{evaluation.campaigns_id}"

    if evaluator and evaluator.email:
        evaluator_name = f"{evaluator.first_name} {evaluator.last_name}".strip()
        subject, html = email_evaluation_sent_to_edit(
            evaluator_name=evaluator_name,
            evaluation_id=evaluation.id,
            campaign_name=campaign_name,
            reviewer_name=actor_name,
            comment=comment,
        )
        await send_email([evaluator.email], subject, html)


# ---------------------------------------------------------------------------
# Trigger: ACTUALIZADO (evaluador reenvía)
# ---------------------------------------------------------------------------

async def _on_updated(
    session: AsyncSession,
    evaluation: Evaluation,
) -> None:
    campaign_name = evaluation.campaign.name if evaluation.campaign else f"#{evaluation.campaigns_id}"
    evaluator_name = ""
    if evaluation.user:
        evaluator_name = f"{evaluation.user.first_name} {evaluation.user.last_name}".strip()

    company_id = evaluation.campaign.company_id if evaluation.campaign else None
    if not company_id:
        return

    reviewers = await _get_company_reviewers(session, company_id)
    reviewer_emails = [r.email for r in reviewers if r.email]
    if not reviewer_emails:
        return

    for reviewer in reviewers:
        if not reviewer.email:
            continue
        reviewer_name = f"{reviewer.first_name} {reviewer.last_name}".strip()
        subject, html = email_evaluation_ready_for_review(
            reviewer_name=reviewer_name,
            evaluation_id=evaluation.id,
            campaign_name=campaign_name,
            evaluator_name=evaluator_name,
        )
        await send_email([reviewer.email], subject, html)
