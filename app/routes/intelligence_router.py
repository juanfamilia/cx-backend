from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.intelligence_model import (
    InsightsPublic,
    InsightUpdate,
    TagsPublic,
    AlertThresholdCreate,
    AlertThresholdUpdate,
    AlertThresholdsPublic,
)
from app.services.intelligence_services import (
    get_insights_for_company,
    mark_insight_as_read,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence & Insights"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/insights")
async def get_company_insights(
    request: Request,
    session: AsyncSession = Depends(get_db),
    unread_only: bool = Query(default=False),
    severity: str | None = Query(default=None),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
) -> InsightsPublic:
    """Get automated insights for the company"""
    
    # Only admins and managers can view insights
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")
    
    company_id = request.state.user.company_id
    if request.state.user.role == 0:
        # Superadmin needs to specify company_id via query param (future enhancement)
        raise PermissionDeniedException(custom_message="specify company_id for superadmin")
    
    insights = await get_insights_for_company(
        session,
        company_id,
        unread_only=unread_only,
        severity=severity,
        offset=offset,
        limit=limit
    )
    
    return insights


@router.put("/insights/{insight_id}/read")
async def mark_insight_read(
    request: Request,
    insight_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Mark an insight as read"""
    
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="update insights")
    
    insight = await mark_insight_as_read(session, insight_id)
    
    # Check ownership (ensure user's company matches insight's company)
    if request.state.user.role != 0 and insight.company_id != request.state.user.company_id:
        raise PermissionDeniedException(custom_message="access this insight")
    
    return insight


@router.get("/insights/summary")
async def get_insights_summary(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get summary of insights by severity"""
    
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")
    
    company_id = request.state.user.company_id
    
    # Get counts by severity
    from sqlmodel import select, func
    from app.models.intelligence_model import Insight
    
    query = (
        select(
            Insight.severity,
            func.count(Insight.id).label("count")
        )
        .where(
            Insight.company_id == company_id,
            Insight.is_read == False,
            Insight.deleted_at == None
        )
        .group_by(Insight.severity)
    )
    
    result = await session.execute(query)
    data = result.all()
    
    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total_unread": 0
    }
    
    for row in data:
        summary[row.severity] = row.count
        summary["total_unread"] += row.count
    
    return summary


@router.get("/insights/top-actions")
async def get_top_suggested_actions(
    request: Request,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, le=20),
):
    """Get most common suggested actions across all insights"""
    
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")
    
    company_id = request.state.user.company_id
    
    from sqlmodel import select
    from app.models.intelligence_model import Insight
    
    # Get all insights with suggested actions
    query = select(Insight).where(
        Insight.company_id == company_id,
        Insight.suggested_actions != None,
        Insight.deleted_at == None
    )
    
    result = await session.execute(query)
    insights = result.scalars().all()
    
    # Count action frequencies
    action_counts = {}
    for insight in insights:
        if insight.suggested_actions:
            for action in insight.suggested_actions:
                action_counts[action] = action_counts.get(action, 0) + 1
    
    # Sort by frequency
    top_actions = sorted(
        action_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return {
        "top_actions": [
            {"action": action, "frequency": count}
            for action, count in top_actions
        ]
    }


@router.get("/insights/trends")
async def get_insight_trends(
    request: Request,
    session: AsyncSession = Depends(get_db),
    days: int = Query(default=30, le=90),
):
    """Get insight trends over time"""
    
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")
    
    company_id = request.state.user.company_id
    
    from datetime import datetime, timedelta
    from sqlmodel import select, func
    from app.models.intelligence_model import Insight
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query insights grouped by date and type
    query = (
        select(
            func.date(Insight.created_at).label("date"),
            Insight.insight_type,
            func.count(Insight.id).label("count")
        )
        .where(
            Insight.company_id == company_id,
            Insight.created_at >= start_date,
            Insight.deleted_at == None
        )
        .group_by(func.date(Insight.created_at), Insight.insight_type)
        .order_by(func.date(Insight.created_at))
    )
    
    result = await session.execute(query)
    data = result.all()
    
    # Format for Chart.js
    trends_by_type = {}
    for row in data:
        if row.insight_type not in trends_by_type:
            trends_by_type[row.insight_type] = {
                "dates": [],
                "counts": []
            }
        trends_by_type[row.insight_type]["dates"].append(str(row.date))
        trends_by_type[row.insight_type]["counts"].append(row.count)
    
    return {
        "labels": list(set(str(row.date) for row in data)),
        "datasets": [
            {
                "label": insight_type.replace("_", " ").title(),
                "data": trends_by_type[insight_type]["counts"]
            }
            for insight_type in trends_by_type
        ]
    }
