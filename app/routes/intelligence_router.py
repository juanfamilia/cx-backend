"""
Intelligence Router for main API service
Provides insights, trends, and analytics endpoints
"""
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from sqlmodel import select, func

from shared.core.db import get_db
from shared.models.intelligence_model import Insight, InsightsPublic
from shared.services.intelligence_services import get_insights_for_company, mark_insight_as_read
from shared.utils.deps import check_company_payment_status, get_auth_user
from shared.utils.exceptions import PermissionDeniedException

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence & Insights"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


def resolve_company_id(user, query_company_id: int | None):
    """Resolve company_id based on user role"""
    if user.role == 0:  # superadmin
        return query_company_id
    return user.company_id


@router.get(
    "/insights",
    response_model=InsightsPublic,
    summary="Obtener insights de la compañía",
)
async def get_company_insights(
    request: Request,
    session: AsyncSession = Depends(get_db),
    unread_only: bool = Query(False),
    severity: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=50),
    company_id: int | None = Query(None),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")

    company_id = resolve_company_id(request.state.user, company_id)
    return await get_insights_for_company(
        session=session,
        company_id=company_id,
        unread_only=unread_only,
        severity=severity,
        offset=offset,
        limit=limit
    )


@router.put("/insights/{insight_id}/read", summary="Marcar insight como leído")
async def mark_insight_read(
    request: Request,
    insight_id: int,
    session: AsyncSession = Depends(get_db),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="update insights")

    insight = await mark_insight_as_read(session, insight_id)

    if request.state.user.role != 0 and insight.company_id != request.state.user.company_id:
        raise PermissionDeniedException(custom_message="access this insight")

    return insight


@router.get("/insights/summary", summary="Resumen de insights por severidad")
async def get_insights_summary(
    request: Request,
    session: AsyncSession = Depends(get_db),
    company_id: int | None = Query(None),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")

    company_id = resolve_company_id(request.state.user, company_id)

    query = (
        select(Insight.severity, func.count(Insight.id).label("count"))
        .where(Insight.deleted_at == None, Insight.company_id == company_id, Insight.is_read == False)
        .group_by(Insight.severity)
    )

    result = await session.execute(query)
    data = result.all()

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total_unread": 0}
    for row in data:
        summary[row.severity] = row.count
        summary["total_unread"] += row.count

    return summary


@router.get("/insights/top-actions", summary="Acciones sugeridas más frecuentes")
async def get_top_suggested_actions(
    request: Request,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(10, le=20),
    company_id: int | None = Query(None),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")

    company_id = resolve_company_id(request.state.user, company_id)

    query = select(Insight).where(
        Insight.deleted_at == None,
        Insight.company_id == company_id,
        Insight.suggested_actions != None
    )

    result = await session.execute(query)
    insights = result.scalars().all()

    action_counts = {}
    for ins in insights:
        if ins.suggested_actions:
            for act in ins.suggested_actions:
                action_counts[act] = action_counts.get(act, 0) + 1

    top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return {"top_actions": [{"action": a, "frequency": c} for a, c in top_actions]}


@router.get("/insights/trends", summary="Tendencias de insights")
async def get_insight_trends(
    request: Request,
    session: AsyncSession = Depends(get_db),
    days: int = Query(30, le=90),
    company_id: int | None = Query(None),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")

    company_id = resolve_company_id(request.state.user, company_id)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    query = (
        select(
            func.date(Insight.created_at).label("date"),
            Insight.insight_type,
            func.count(Insight.id).label("count")
        )
        .where(
            Insight.deleted_at == None,
            Insight.company_id == company_id,
            Insight.created_at >= start_date
        )
        .group_by(func.date(Insight.created_at), Insight.insight_type)
        .order_by(func.date(Insight.created_at))
    )

    result = await session.execute(query)
    data = result.all()

    trends_by_type = {}
    for row in data:
        trends_by_type.setdefault(row.insight_type, {"dates": [], "counts": []})
        trends_by_type[row.insight_type]["dates"].append(str(row.date))
        trends_by_type[row.insight_type]["counts"].append(row.count)

    return {
        "labels": sorted(set(str(row.date) for row in data)),
        "datasets": [
            {"label": t.replace("_", " ").title(), "data": trends_by_type[t]["counts"]}
            for t in trends_by_type
        ],
    }
