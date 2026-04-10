from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.interaction_phase_services import (
    InteractionPhasesPublic,
    get_interaction_phases,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/interaction-phases",
    tags=["Interaction Phases"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation/{evaluation_id}", response_model=InteractionPhasesPublic)
async def get_phases(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> InteractionPhasesPublic:
    """
    Devuelve las fases de negocio detectadas por IA para una evaluación:
    ENTRY → ATTENTION → CLOSURE (+ WAITING, ESCALATION si aplica).
    Cada fase incluye timestamp de inicio/fin y resumen del momento.
    Permite navegación semántica en el reproductor de video.
    """
    from app.services.evaluation_services import get_evaluation

    evaluation = await get_evaluation(session, evaluation_id)
    user = request.state.user
    if user.role != 0 and (
        evaluation.campaign is None
        or evaluation.campaign.company_id != user.company_id
    ):
        raise PermissionDeniedException(custom_message="access this evaluation")

    return await get_interaction_phases(session, evaluation_id)
