"""
Executive Dashboard Router
Endpoints for executive analytics and insights
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException
from app.services.executive_dashboard_services import (
    get_executive_metrics,
    ExecutiveDashboardResponse,
)


router = APIRouter(
    prefix="/executive",
    tags=["Executive Dashboard"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/metrics", response_model=ExecutiveDashboardResponse)
async def get_dashboard_metrics(
    request: Request,
    company_id: Optional[int] = Query(
        None,
        description="Company to scope metrics (required for role 0 if the user has no company_id)",
    ),
    branch_id: Optional[str] = Query(None, description="Filter by branch ID"),
    country: Optional[str] = Query(None, description="Filter by country"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get executive dashboard metrics
    
    Returns aggregated KPIs across all interactions:
    - Average NPS, CES, Service Quality
    - Greeting rate, Product offer rate, Resolution rate
    - Churn risk rate
    - Emotion distribution
    - Metrics by branch
    
    All metrics are filterable by branch, country, date range, and interaction type.
    """
    user = request.state.user
    if user.role != 0:
        if user.company_id is None:
            raise PermissionDeniedException(custom_message="access executive metrics")
        effective_company_id = user.company_id
    else:
        effective_company_id = company_id or user.company_id
        if effective_company_id is None:
            raise PermissionDeniedException(
                custom_message=(
                    "access executive metrics: pass company_id query or use a user "
                    "linked to a company"
                )
            )

    return await get_executive_metrics(
        session=session,
        company_id=effective_company_id,
        branch_id=branch_id,
        country=country,
        start_date=start_date,
        end_date=end_date,
        interaction_type=interaction_type,
    )
