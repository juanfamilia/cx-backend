from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.gap_analysis_services import (
    GapAnalysisResult,
    compute_gap_analysis,
    get_gap_summary_for_campaign,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/gap-analysis",
    tags=["Gap Analysis"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation/{evaluation_id}", response_model=GapAnalysisResult)
async def get_evaluation_gap(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> GapAnalysisResult:
    """
    Contrasta las respuestas del auditor con los campos IA para una evaluación.
    Devuelve discrepancias clasificadas por severidad y score de confiabilidad.
    """
    from app.services.evaluation_services import get_evaluation

    evaluation = await get_evaluation(session, evaluation_id)
    user = request.state.user
    if user.role != 0 and (
        evaluation.campaign is None
        or evaluation.campaign.company_id != user.company_id
    ):
        raise PermissionDeniedException(custom_message="access this evaluation")

    return await compute_gap_analysis(session, evaluation_id)


@router.get("/campaign/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign_gap_summary(
    request: Request,
    campaign_id: int,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Agrega el Gap Analysis de todas las evaluaciones de una campaña.
    Muestra promedio de fiabilidad, total de discrepancias críticas
    y ranking de los campos con más discrepancias.
    """
    user = request.state.user
    company_id = None if user.role == 0 else user.company_id
    return await get_gap_summary_for_campaign(session, campaign_id, company_id)
