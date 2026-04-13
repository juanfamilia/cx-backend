from sqlalchemy import text
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
        CompanyCampaignAnalysis.company_id == company_id
    )
    result_analysis = await session.scalars(queryCompanyAnalysis)
    analysis_summary = result_analysis.all()

    return {"summary": summary, "analysis": analysis_summary}


async def get_manager_summary(
    session: AsyncSession, company_id: int, user_id: int
) -> dict:
    statement = select(ManagerSummary).where(ManagerSummary.user_id == user_id)
    result = await session.scalars(statement)
    summary_row = result.first()

    analysis_sql = text(
        """
        SELECT DISTINCT ON (cca.campaign_id)
            cca.company_id,
            cca.campaign_id,
            cca.campaign_name,
            cca.operative_views
        FROM company_campaign_analysis cca
        INNER JOIN campaign_zones cz
            ON cz.campaign_id = cca.campaign_id AND cz.deleted_at IS NULL
        INNER JOIN user_zones uz
            ON uz.zone_id = cz.zone_id
            AND uz.user_id = :user_id
            AND uz.deleted_at IS NULL
        WHERE cca.company_id = :company_id
        ORDER BY cca.campaign_id
        """
    )
    analysis_result = await session.execute(
        analysis_sql, {"user_id": user_id, "company_id": company_id}
    )
    analysis_list = [dict(row) for row in analysis_result.mappings().all()]

    # Verificar si el gerente tiene zonas asignadas
    has_zones_sql = text(
        "SELECT COUNT(*) FROM user_zones WHERE user_id = :manager_id AND deleted_at IS NULL"
    )
    has_zones_result = await session.execute(has_zones_sql, {"manager_id": user_id})
    has_zones = (has_zones_result.scalar() or 0) > 0

    if has_zones:
        # Filtrar solo por evaluaciones en las zonas del gerente
        counts_sql = text(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE e.status::text IN ('APROVED', 'aprobado')
                ) AS evaluaciones_aprobadas,
                COUNT(*) FILTER (
                    WHERE e.status::text IN ('REJECTED', 'rechazado')
                ) AS evaluaciones_rechazadas
            FROM evaluations e
            INNER JOIN users u ON u.id = e.user_id AND u.deleted_at IS NULL
            INNER JOIN user_zones ez ON ez.user_id = u.id AND ez.deleted_at IS NULL
            INNER JOIN user_zones mz
                ON mz.zone_id = ez.zone_id
                AND mz.user_id = :manager_id
                AND mz.deleted_at IS NULL
            WHERE e.deleted_at IS NULL
              AND u.company_id = :company_id
              AND u.role = 3
            """
        )
        counts_result = await session.execute(
            counts_sql, {"manager_id": user_id, "company_id": company_id}
        )
    else:
        # Sin zonas configuradas: mostrar totales de la empresa
        counts_sql = text(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE e.status::text IN ('APROVED', 'aprobado')
                ) AS evaluaciones_aprobadas,
                COUNT(*) FILTER (
                    WHERE e.status::text IN ('REJECTED', 'rechazado')
                ) AS evaluaciones_rechazadas
            FROM evaluations e
            INNER JOIN users u ON u.id = e.user_id AND u.deleted_at IS NULL
            WHERE e.deleted_at IS NULL
              AND u.company_id = :company_id
              AND u.role = 3
            """
        )
        counts_result = await session.execute(
            counts_sql, {"company_id": company_id}
        )

    counts_row = counts_result.mappings().first()
    eval_ok = int(counts_row["evaluaciones_aprobadas"] or 0) if counts_row else 0
    eval_rej = int(counts_row["evaluaciones_rechazadas"] or 0) if counts_row else 0

    # Si no tiene zonas, también completar active_campaigns desde la tabla directamente
    if not has_zones and (summary_row is None or summary_row.active_campaigns == 0):
        active_camps_sql = text(
            """
            SELECT COUNT(*) FROM campaigns
            WHERE company_id = :company_id
              AND deleted_at IS NULL
              AND date_start <= CURRENT_DATE
              AND date_end >= CURRENT_DATE
            """
        )
        ac_result = await session.execute(active_camps_sql, {"company_id": company_id})
        active_campaigns_fallback = int(ac_result.scalar() or 0)
    else:
        active_campaigns_fallback = None

    summary_dict = {
        "user_id": user_id,
        "company_id": company_id,
        "zonas_asignadas": 0,
        "evaluadores_asignados": 0,
        "active_campaigns": active_campaigns_fallback if active_campaigns_fallback is not None else 0,
        "evaluaciones_aprobadas": eval_ok,
        "evaluaciones_rechazadas": eval_rej,
    }
    if summary_row:
        dumped = summary_row.model_dump()
        for key in (
            "user_id",
            "company_id",
            "zonas_asignadas",
            "evaluadores_asignados",
            "active_campaigns",
        ):
            if dumped.get(key) is not None:
                summary_dict[key] = dumped[key]

    # Si zones fallback existe y el view devolvió 0 en active_campaigns, usar el fallback
    if active_campaigns_fallback is not None and summary_dict.get("active_campaigns", 0) == 0:
        summary_dict["active_campaigns"] = active_campaigns_fallback

    return {"summary": summary_dict, "analysis": analysis_list}


async def get_superadmin_summary(session: AsyncSession) -> SuperadminSummary:

    statement = select(SuperadminSummary)
    result = await session.scalars(statement)
    summary = result.first()

    if not summary:
        raise NotFoundException("Data not found")

    return summary
