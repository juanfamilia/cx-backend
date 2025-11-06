from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.charts_campaign_views import (
    CampaignGoalsCoverage,
    CampaignGoalsWeeklyProgress,
)
from app.models.user_evaluation_summary_model import (
    CompanyUserEvaluation,
    ManagerSummary,
    SuperadminSummary,
    UserEvaluationSummary,
)
from app.utils.exeptions import NotFoundException


async def get_user_evaluation_summary(session: AsyncSession, user_id: int) -> dict:

    statement = select(UserEvaluationSummary).where(
        UserEvaluationSummary.user_id == user_id
    )
    result = await session.scalars(statement)
    summary = result.first()

    query_weekly = select(CampaignGoalsWeeklyProgress).where(
        CampaignGoalsWeeklyProgress.evaluator_id == user_id
    )
    result_weekly = await session.scalars(query_weekly)
    weekly_summary = result_weekly.all()

    query_coverage = select(CampaignGoalsCoverage).where(
        CampaignGoalsCoverage.evaluator_id == user_id
    )
    result_coverage = await session.scalars(query_coverage)
    coverage_summary = result_coverage.first()

    return {
        "summary": summary,
        "weekly_progress": weekly_summary,
        "coverage": coverage_summary,
    }


async def get_company_users_evaluations(
    session: AsyncSession, company_id: int
) -> CompanyUserEvaluation:

    statement = select(CompanyUserEvaluation).where(
        CompanyUserEvaluation.company_id == company_id
    )
    result = await session.scalars(statement)
    summary = result.first()

    if not summary:
        raise NotFoundException("Data not found")

    return summary


async def get_manager_summary(session: AsyncSession, company_id: int) -> ManagerSummary:

    statement = select(ManagerSummary).where(ManagerSummary.company_id == company_id)
    result = await session.scalars(statement)
    summary = result.first()

    if not summary:
        raise NotFoundException("Data not found")

    return summary


async def get_superadmin_summary(session: AsyncSession) -> SuperadminSummary:

    statement = select(SuperadminSummary)
    result = await session.scalars(statement)
    summary = result.first()

    if not summary:
        raise NotFoundException("Data not found")

    return summary
