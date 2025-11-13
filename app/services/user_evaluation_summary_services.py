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
from app.models.company_campaign_analysis import (
    CompanyCampaignAnalysis,
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
    coverage_summary = result_coverage.all()

    return {
        "summary": summary,
        "weekly_progress": weekly_summary,
        "coverage": coverage_summary,
    }


async def get_company_users_evaluations(session: AsyncSession, company_id: int) -> dict:

    queryCompanyUser = select(CompanyUserEvaluation).where(
        CompanyUserEvaluation.company_id == company_id
    )
    result = await session.scalars(queryCompanyUser)
    summary = result.first()

    queryCompanyAnalysis = select(CompanyCampaignAnalysis).where(
        CompanyUserEvaluation.company_id == company_id
    )
    result_analysis = await session.scalars(queryCompanyAnalysis)
    analysis_summary = result_analysis.all()

    return {"summary": summary, "analysis": analysis_summary}


async def get_manager_summary(
    session: AsyncSession, company_id: int, user_id: int
) -> ManagerSummary:

    statement = select(ManagerSummary).where(ManagerSummary.company_id == company_id)
    result = await session.scalars(statement)
    summary = result.first()

    custom_query = """
    SELECT *
    FROM company_campaign_analysis_agg cca
    JOIN campaign_zones cz ON cz.campaign_id = cca.campaign_id
    JOIN user_zones uz ON uz.zone_id = cz.zone_id
    WHERE uz.user_id = :user_id
      AND cz.deleted_at IS NULL
      AND uz.deleted_at IS NULL
    """
    result_analysis = await session.execute(custom_query, {"user_id": user_id}).all()

    return {"summary": summary, "analysis": result_analysis}


async def get_superadmin_summary(session: AsyncSession) -> SuperadminSummary:

    statement = select(SuperadminSummary)
    result = await session.scalars(statement)
    summary = result.first()

    if not summary:
        raise NotFoundException("Data not found")

    return summary
