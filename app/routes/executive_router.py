"""
Executive Dashboard Router
Endpoints for executive analytics and insights
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.utils.deps import get_auth_user
from app.models.user_model import UserPublic
from app.services.executive_dashboard_services import (
    get_executive_metrics,
    ExecutiveDashboardResponse,
)


router = APIRouter(
    prefix="/executive",
    tags=["Executive Dashboard"],
)


@router.get("/metrics", response_model=ExecutiveDashboardResponse)
async def get_dashboard_metrics(
    branch_id: Optional[str] = Query(None, description="Filter by branch ID"),
    country: Optional[str] = Query(None, description="Filter by country"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    session: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_auth_user),
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
    company_id = current_user.company_id if hasattr(current_user, 'company_id') else None
    
    if not company_id:
        # For admin users, might need different handling
        company_id = 1  # Default fallback
    
    return await get_executive_metrics(
        session=session,
        company_id=company_id,
        branch_id=branch_id,
        country=country,
        start_date=start_date,
        end_date=end_date,
        interaction_type=interaction_type,
    )
