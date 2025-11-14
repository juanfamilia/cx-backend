from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from sqlmodel import select, func

from app.core.db import get_db
from app.models.intelligence_model import Insight, InsightsPublic
from app.services.intelligence_services import get_insights_for_company, mark_insight_as_read
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence & Insights"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)

# ---------------------- Helper multi-tenant ---------------------- #
def resolve_company_id(user, query_company_id: int | None):
    """
    Devuelve el company_id correcto según el rol.
    Superadmin puede pasar cualquier company_id o None para todas las compañías.
    Usuarios normales usan siempre su propia compañía.
    """
    if user.role == 0:  # superadmin
        return query_company_id
    return user.company_id

# ---------------------- GET /insights ---------------------- #
@router.get(
    "/insights",
    response_model=InsightsPublic,
    summary="Obtener insights de la compañía",
    description="Devuelve los insights automáticos de la compañía. Superadmin puede filtrar por company_id."
)
async def get_company_insights(
    request: Request,
    session: AsyncSession = Depends(get_db),
    unread_only: bool = Query(False, description="Filtrar solo insights no leídos"),
    severity: str | None = Query(None, description="Filtrar por severidad: critical, high, medium, low"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(10, le=50, description="Número máximo de registros"),
    company_id: int | None = Query(None, description="Solo para superadmin"),
):
    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="view insights")

    company_id = resolve_company_id(request.state.user, company_id)

    insights = await get_insights_for_company(
        session=session,
        company_id=company_id,
        unread_only=unread_only,
        severity=severity,
        offset=offset,
        limit=limit
    )
    return insights

# ---------------------- PUT /insights/{id}/read ---------------------- #
@router.put(
    "/insights/{insight_id}/read",
    summary="Marcar insight como leído",
    description="Marca un insight como leído. Solo admins, managers o superadmin pueden hacerlo."
)
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

# ---------------------- GET /insights/summary ---------------------- #
@router.get(
    "/insights/summary",
    summary="Resumen de insights por severidad",
    description="Devuelve un resumen con conteo de insights por severidad y total no leídos."
)
async def get_insights_summary(
    request: Request,
    session: AsyncSession = Depends(get_db),
    company_id: int | None = Query(None, description="Solo para superadmin"),
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

# ---------------------- GET /insights/top-actions ---------------------- #
@router.get(
    "/insights/top-actions",
    summary="Acciones sugeridas más frecuentes",
    description="Devuelve las acciones sugeridas más comunes en todos los insights de la compañía."
)
async def get_top_suggested_actions(
    request: Request,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(10, le=20, description="Número máximo de acciones"),
    company_id: int | None = Query(None, description="Solo para superadmin"),
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

# ---------------------- GET /insights/trends ---------------------- #
@router.get(
    "/insights/trends",
    summary="Tendencias de insights",
    description="Devuelve la evolución de insights por tipo durante los últimos N días."
)
async def get_insight_trends(
    request: Request,
    session: AsyncSession = Depends(get_db),
    days: int = Query(30, le=90, description="Número de días atrás para el análisis"),
    company_id: int | None = Query(None, description="Solo para superadmin"),
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
