"""
Executive Dashboard Services
Aggregated metrics and analytics for executive insights
"""
from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, and_

from app.models.evaluation_model import Evaluation
from app.models.campaign_model import Campaign


class ExecutiveMetrics(BaseModel):
    """Aggregated executive metrics"""
    total_interactions: int
    avg_nps: Optional[float]
    avg_ces: Optional[float]
    avg_service_quality: Optional[float]
    greeting_rate: Optional[float]  # % with greeting
    product_offer_rate: Optional[float]  # % with product offered
    resolution_rate: Optional[float]  # % with problem resolved
    churn_risk_rate: Optional[float]  # % with high churn risk (>70)
    
    # Emotion distribution
    positive_interactions: int
    negative_interactions: int
    neutral_interactions: int


class BranchMetrics(BaseModel):
    """Metrics grouped by branch"""
    branch_id: str
    branch_name: Optional[str]
    interaction_count: int
    avg_nps: Optional[float]
    avg_ces: Optional[float]
    avg_service_quality: Optional[float]


class ExecutiveDashboardResponse(BaseModel):
    """Full executive dashboard response"""
    metrics: ExecutiveMetrics
    branches: List[BranchMetrics]
    date_range: dict


async def get_executive_metrics(
    session: AsyncSession,
    company_id: int,
    branch_id: Optional[str] = None,
    country: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    interaction_type: Optional[str] = None,
) -> ExecutiveDashboardResponse:
    """
    Get aggregated executive metrics with optional filters
    """
    # Build base query with company filter via campaign
    base_conditions = [
        Campaign.company_id == company_id,
        Evaluation.deleted_at.is_(None),
    ]
    
    if branch_id:
        base_conditions.append(Evaluation.branch_id == branch_id)
    if country:
        base_conditions.append(Evaluation.country == country)
    if start_date:
        base_conditions.append(Evaluation.interaction_date >= start_date)
    if end_date:
        base_conditions.append(Evaluation.interaction_date <= end_date)
    if interaction_type:
        base_conditions.append(Evaluation.interaction_type == interaction_type)
    
    # Get aggregated metrics
    metrics_query = (
        select(
            func.count(Evaluation.id).label('total'),
            func.avg(Evaluation.nps_inferred).label('avg_nps'),
            func.avg(Evaluation.customer_effort_score).label('avg_ces'),
            func.avg(Evaluation.service_quality_score).label('avg_quality'),
            func.sum(func.cast(Evaluation.greeting_detected, Integer)).label('greeting_count'),
            func.sum(func.cast(Evaluation.product_offered, Integer)).label('offer_count'),
            func.sum(func.cast(Evaluation.problem_resolved, Integer)).label('resolved_count'),
            func.count(Evaluation.id).filter(Evaluation.risk_of_churn > 70).label('high_risk_count'),
        )
        .select_from(Evaluation)
        .join(Campaign, Evaluation.campaigns_id == Campaign.id)
        .where(and_(*base_conditions))
    )
    
    result = await session.execute(metrics_query)
    row = result.one()
    
    total = row.total or 0
    
    # Calculate emotion distribution
    emotion_query = (
        select(
            func.count(Evaluation.id).filter(
                Evaluation.customer_emotion.in_(['satisfecho', 'contento', 'feliz', 'positivo'])
            ).label('positive'),
            func.count(Evaluation.id).filter(
                Evaluation.customer_emotion.in_(['frustrado', 'molesto', 'enojado', 'negativo'])
            ).label('negative'),
            func.count(Evaluation.id).filter(
                Evaluation.customer_emotion.in_(['neutral', 'indiferente'])
            ).label('neutral'),
        )
        .select_from(Evaluation)
        .join(Campaign, Evaluation.campaigns_id == Campaign.id)
        .where(and_(*base_conditions))
    )
    
    emotion_result = await session.execute(emotion_query)
    emotion_row = emotion_result.one()
    
    metrics = ExecutiveMetrics(
        total_interactions=total,
        avg_nps=round(row.avg_nps, 1) if row.avg_nps else None,
        avg_ces=round(row.avg_ces, 1) if row.avg_ces else None,
        avg_service_quality=round(row.avg_quality, 1) if row.avg_quality else None,
        greeting_rate=round((row.greeting_count / total) * 100, 1) if total > 0 and row.greeting_count else None,
        product_offer_rate=round((row.offer_count / total) * 100, 1) if total > 0 and row.offer_count else None,
        resolution_rate=round((row.resolved_count / total) * 100, 1) if total > 0 and row.resolved_count else None,
        churn_risk_rate=round((row.high_risk_count / total) * 100, 1) if total > 0 else None,
        positive_interactions=emotion_row.positive or 0,
        negative_interactions=emotion_row.negative or 0,
        neutral_interactions=emotion_row.neutral or 0,
    )
    
    # Get branch breakdown
    branch_query = (
        select(
            Evaluation.branch_id,
            Evaluation.branch_name,
            func.count(Evaluation.id).label('count'),
            func.avg(Evaluation.nps_inferred).label('avg_nps'),
            func.avg(Evaluation.customer_effort_score).label('avg_ces'),
            func.avg(Evaluation.service_quality_score).label('avg_quality'),
        )
        .select_from(Evaluation)
        .join(Campaign, Evaluation.campaigns_id == Campaign.id)
        .where(and_(*base_conditions, Evaluation.branch_id.isnot(None)))
        .group_by(Evaluation.branch_id, Evaluation.branch_name)
        .order_by(func.count(Evaluation.id).desc())
        .limit(20)
    )
    
    branch_result = await session.execute(branch_query)
    branches = [
        BranchMetrics(
            branch_id=row.branch_id,
            branch_name=row.branch_name,
            interaction_count=row.count,
            avg_nps=round(row.avg_nps, 1) if row.avg_nps else None,
            avg_ces=round(row.avg_ces, 1) if row.avg_ces else None,
            avg_service_quality=round(row.avg_quality, 1) if row.avg_quality else None,
        )
        for row in branch_result.all()
    ]
    
    return ExecutiveDashboardResponse(
        metrics=metrics,
        branches=branches,
        date_range={
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        }
    )


# Import for type hints
from sqlalchemy import Integer
