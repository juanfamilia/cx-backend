from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.evaluation_analysis_model import EvaluationAnalysisPublic
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/evaluations-analysis",
    tags=["Evaluations Analysis"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation-analysis/{evaluation_id}")
async def get_evaluation_analysis(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> EvaluationAnalysisPublic:

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve this analysis")

    analysis = await get_evaluation_analysis(session, evaluation_id)

    return analysis
