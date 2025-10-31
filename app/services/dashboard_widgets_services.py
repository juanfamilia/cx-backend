"""
Dashboard Widget Data Providers
Provides data for various dashboard widgets
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import Any

from app.models.evaluation_model import Evaluation, StatusEnum
from app.models.evaluation_analysis_model import EvaluationAnalysis
from app.models.campaign_model import Campaign
from app.models.user_model import User
from app.models.company_model import Company
import json


async def get_nps_trend_data(
    session: AsyncSession,
    company_id: int | None = None,
    days: int = 30
) -> dict:
    """Get NPS trend data for the last N days"""
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query evaluations with analysis
    query = (
        select(
            func.date(Evaluation.created_at).label("date"),
            func.avg(
                func.cast(
                    func.json_extract_path_text(
                        EvaluationAnalysis.operative_view,
                        "NPS", "score"
                    ),
                    sa.Float
                )
            ).label("avg_nps")
        )
        .join(EvaluationAnalysis, Evaluation.id == EvaluationAnalysis.evaluation_id)
        .where(
            Evaluation.created_at >= start_date,
            Evaluation.deleted_at == None,
            EvaluationAnalysis.operative_view != None
        )
    )
    
    if company_id:
        query = query.join(Campaign).where(Campaign.company_id == company_id)
    
    query = query.group_by(func.date(Evaluation.created_at)).order_by(func.date(Evaluation.created_at))
    
    result = await session.execute(query)
    data = result.all()
    
    return {
        "labels": [str(row.date) for row in data],
        "datasets": [
            {
                "label": "NPS Score",
                "data": [float(row.avg_nps) if row.avg_nps else 0 for row in data],
                "borderColor": "#8b5cf6",
                "backgroundColor": "rgba(139, 92, 246, 0.1)",
            }
        ]
    }


async def get_status_breakdown_data(
    session: AsyncSession,
    company_id: int | None = None
) -> dict:
    """Get evaluation status breakdown for pie chart"""
    
    query = (
        select(
            Evaluation.status,
            func.count(Evaluation.id).label("count")
        )
        .where(Evaluation.deleted_at == None)
    )
    
    if company_id:
        query = query.join(Campaign).where(Campaign.company_id == company_id)
    
    query = query.group_by(Evaluation.status)
    
    result = await session.execute(query)
    data = result.all()
    
    # Map status to display names and colors
    status_map = {
        "completed": {"label": "Completed", "color": "#10b981"},
        "pending": {"label": "Pending", "color": "#f59e0b"},
        "analyzing": {"label": "Analyzing", "color": "#3b82f6"},
    }
    
    labels = []
    values = []
    colors = []
    
    for row in data:
        status_info = status_map.get(row.status, {"label": row.status, "color": "#6b7280"})
        labels.append(status_info["label"])
        values.append(row.count)
        colors.append(status_info["color"])
    
    return {
        "labels": labels,
        "datasets": [
            {
                "data": values,
                "backgroundColor": colors,
            }
        ]
    }


async def get_top_evaluators_data(
    session: AsyncSession,
    company_id: int | None = None,
    limit: int = 5
) -> list[dict]:
    """Get top evaluators by evaluation count"""
    
    query = (
        select(
            User.id,
            User.first_name,
            User.last_name,
            func.count(Evaluation.id).label("evaluation_count")
        )
        .join(Evaluation, User.id == Evaluation.user_id)
        .where(
            Evaluation.deleted_at == None,
            User.deleted_at == None
        )
    )
    
    if company_id:
        query = query.where(User.company_id == company_id)
    
    query = (
        query.group_by(User.id, User.first_name, User.last_name)
        .order_by(func.count(Evaluation.id).desc())
        .limit(limit)
    )
    
    result = await session.execute(query)
    data = result.all()
    
    return [
        {
            "id": row.id,
            "name": f"{row.first_name} {row.last_name}",
            "evaluation_count": row.evaluation_count
        }
        for row in data
    ]


async def get_companies_summary_data(
    session: AsyncSession
) -> list[dict]:
    """Get summary data for all companies (superadmin only)"""
    
    query = (
        select(
            Company.id,
            Company.name,
            func.count(Evaluation.id).label("total_evaluations"),
            func.count(
                func.nullif(Evaluation.status == "pending", False)
            ).label("pending_evaluations")
        )
        .outerjoin(Campaign, Company.id == Campaign.company_id)
        .outerjoin(Evaluation, Campaign.id == Evaluation.campaigns_id)
        .where(Company.deleted_at == None)
        .group_by(Company.id, Company.name)
        .order_by(func.count(Evaluation.id).desc())
    )
    
    result = await session.execute(query)
    data = result.all()
    
    return [
        {
            "company_id": row.id,
            "company_name": row.name,
            "total_evaluations": row.total_evaluations or 0,
            "pending_evaluations": row.pending_evaluations or 0
        }
        for row in data
    ]


async def get_manager_campaigns_data(
    session: AsyncSession,
    user_id: int
) -> list[dict]:
    """Get campaigns assigned to a manager"""
    
    # This would typically query campaign_assignments
    # For now, simplified query
    query = (
        select(Campaign)
        .where(
            Campaign.deleted_at == None
        )
        .order_by(Campaign.created_at.desc())
        .limit(10)
    )
    
    result = await session.execute(query)
    campaigns = result.scalars().all()
    
    return [
        {
            "id": campaign.id,
            "name": campaign.name,
            "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        }
        for campaign in campaigns
    ]


async def get_shopper_campaigns_data(
    session: AsyncSession,
    user_id: int
) -> list[dict]:
    """Get active campaigns for a shopper"""
    
    # Query campaigns where user is assigned
    query = (
        select(Campaign)
        .where(
            Campaign.deleted_at == None,
            Campaign.end_date >= datetime.now()
        )
        .order_by(Campaign.end_date.asc())
        .limit(5)
    )
    
    result = await session.execute(query)
    campaigns = result.scalars().all()
    
    return [
        {
            "id": campaign.id,
            "name": campaign.name,
            "deadline": campaign.end_date.isoformat() if campaign.end_date else None,
        }
        for campaign in campaigns
    ]


async def get_evaluation_by_month_data(
    session: AsyncSession,
    company_id: int | None = None,
    months: int = 6
) -> dict:
    """Get evaluation count by month for bar chart"""
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    query = (
        select(
            func.to_char(Evaluation.created_at, "YYYY-MM").label("month"),
            func.count(Evaluation.id).label("count")
        )
        .where(
            Evaluation.created_at >= start_date,
            Evaluation.deleted_at == None
        )
    )
    
    if company_id:
        query = query.join(Campaign).where(Campaign.company_id == company_id)
    
    query = (
        query.group_by(func.to_char(Evaluation.created_at, "YYYY-MM"))
        .order_by(func.to_char(Evaluation.created_at, "YYYY-MM"))
    )
    
    result = await session.execute(query)
    data = result.all()
    
    return {
        "labels": [row.month for row in data],
        "datasets": [
            {
                "label": "Evaluations",
                "data": [row.count for row in data],
                "backgroundColor": "#3b82f6",
            }
        ]
    }


async def get_ioc_ird_ces_averages(
    session: AsyncSession,
    company_id: int | None = None
) -> dict:
    """Get average IOC, IRD, CES scores"""
    
    query = select(EvaluationAnalysis.operative_view).where(
        EvaluationAnalysis.operative_view != None,
        EvaluationAnalysis.deleted_at == None
    )
    
    if company_id:
        query = (
            query.join(Evaluation)
            .join(Campaign)
            .where(Campaign.company_id == company_id)
        )
    
    result = await session.execute(query)
    analyses = result.scalars().all()
    
    ioc_scores = []
    ird_scores = []
    ces_scores = []
    
    for analysis in analyses:
        try:
            data = json.loads(analysis) if isinstance(analysis, str) else analysis
            if "IOC" in data and "score" in data["IOC"]:
                ioc_scores.append(data["IOC"]["score"])
            if "IRD" in data and "score" in data["IRD"]:
                ird_scores.append(data["IRD"]["score"])
            if "CES" in data and "score" in data["CES"]:
                ces_scores.append(data["CES"]["score"])
        except:
            continue
    
    return {
        "IOC": sum(ioc_scores) / len(ioc_scores) if ioc_scores else 0,
        "IRD": sum(ird_scores) / len(ird_scores) if ird_scores else 0,
        "CES": sum(ces_scores) / len(ces_scores) if ces_scores else 0,
    }
