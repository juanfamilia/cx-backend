"""
Intelligence Engine Services
Automated insight generation, tagging, and trend analysis
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
import json
from typing import Any

from app.models.intelligence_model import (
    Insight,
    InsightCreate,
    InsightPublic,
    InsightsPublic,
    Tag,
    TagPublic,
    TagsPublic,
    EvaluationTag,
    EvaluationTagPublic,
    AlertThreshold,
    AlertThresholdPublic,
    AlertThresholdsPublic,
    Trend,
    TrendPublic,
    TrendsPublic,
)
from app.models.evaluation_analysis_model import EvaluationAnalysis
from app.models.evaluation_model import Evaluation
from app.models.campaign_model import Campaign
from app.utils.exeptions import NotFoundException


# ===== INSIGHT GENERATION =====

async def generate_insights_from_analysis(
    session: AsyncSession,
    evaluation_id: int,
    analysis: EvaluationAnalysis,
    company_id: int
) -> list[InsightPublic]:
    """
    Automatically generate insights from evaluation analysis
    
    Analyzes operative_view JSON and creates insights for:
    - High IRD (churn risk)
    - High CES (customer effort)
    - Low IOC (missed opportunities)
    - Quality issues (missing calidad checks)
    - Negative verbatims
    """
    
    insights = []
    
    if not analysis.operative_view:
        return insights
    
    try:
        operative_data = json.loads(analysis.operative_view) if isinstance(analysis.operative_view, str) else analysis.operative_view
    except:
        return insights
    
    # Check IRD (Índice de Riesgo de Deserción)
    ird = operative_data.get("IRD", {})
    if ird.get("score", 0) > 70:
        insight = InsightCreate(
            company_id=company_id,
            evaluation_id=evaluation_id,
            insight_type="ird_alert",
            severity="high" if ird["score"] > 85 else "medium",
            title=f"Alto Riesgo de Deserción - Score: {ird['score']}",
            description=f"Cliente muestra señales de insatisfacción. {ird.get('justificacion', '')}",
            metrics={"IRD": ird["score"]},
            suggested_actions=operative_data.get("acciones_sugeridas", [])
        )
        db_insight = Insight(**insight.model_dump())
        session.add(db_insight)
        insights.append(insight)
    
    # Check CES (Customer Effort Score)
    ces = operative_data.get("CES", {})
    if ces.get("score", 0) > 60:
        insight = InsightCreate(
            company_id=company_id,
            evaluation_id=evaluation_id,
            insight_type="ces_alert",
            severity="medium" if ces["score"] > 75 else "low",
            title=f"Alto Esfuerzo del Cliente - Score: {ces['score']}",
            description=f"El proceso fue complicado para el cliente. {ces.get('justificacion', '')}",
            metrics={"CES": ces["score"]},
            suggested_actions=["Simplificar procesos de información", "Capacitar en eficiencia operativa"]
        )
        db_insight = Insight(**insight.model_dump())
        session.add(db_insight)
        insights.append(insight)
    
    # Check IOC (Índice de Oportunidad Comercial)
    ioc = operative_data.get("IOC", {})
    if ioc.get("score", 0) < 40:
        insight = InsightCreate(
            company_id=company_id,
            evaluation_id=evaluation_id,
            insight_type="opportunity",
            severity="low",
            title=f"Oportunidad Comercial Desaprovechada - Score: {ioc['score']}",
            description=f"Oportunidad de venta no identificada o mal gestionada. {ioc.get('justificacion', '')}",
            metrics={"IOC": ioc["score"]},
            suggested_actions=["Capacitar en prospección de productos", "Revisar técnicas de venta"]
        )
        db_insight = Insight(**insight.model_dump())
        session.add(db_insight)
        insights.append(insight)
    
    # Check Calidad (Quality Checks)
    calidad = operative_data.get("Calidad", {})
    missing_quality = []
    for check, value in calidad.items():
        if not value:
            missing_quality.append(check)
    
    if len(missing_quality) >= 2:
        insight = InsightCreate(
            company_id=company_id,
            evaluation_id=evaluation_id,
            insight_type="quality_issue",
            severity="medium" if len(missing_quality) >= 3 else "low",
            title=f"Deficiencias en Calidad Básica - {len(missing_quality)} puntos",
            description=f"Aspectos faltantes: {', '.join(missing_quality)}",
            metrics={"missing_quality_checks": len(missing_quality)},
            suggested_actions=["Reforzar protocolo de atención básica", "Entrenamiento en estándares de calidad"]
        )
        db_insight = Insight(**insight.model_dump())
        session.add(db_insight)
        insights.append(insight)
    
    # Check Critical Verbatims
    verbatims = operative_data.get("Verbatims", {})
    critical_verbatims = verbatims.get("criticos", [])
    
    if critical_verbatims:
        insight = InsightCreate(
            company_id=company_id,
            evaluation_id=evaluation_id,
            insight_type="quality_issue",
            severity="critical",
            title="Comentarios Críticos Detectados",
            description=f"Se detectaron {len(critical_verbatims)} frases críticas que requieren atención inmediata.",
            metrics={"critical_verbatims_count": len(critical_verbatims)},
            suggested_actions=["Revisión inmediata del caso", "Contactar al cliente", "Plan de acción correctiva"]
        )
        db_insight = Insight(**insight.model_dump())
        session.add(db_insight)
        insights.append(insight)
    
    await session.commit()
    
    return insights


async def get_insights_for_company(
    session: AsyncSession,
    company_id: int,
    unread_only: bool = False,
    severity: str | None = None,
    offset: int = 0,
    limit: int = 10
) -> InsightsPublic:
    """Get insights for a company with filters"""
    
    query = select(Insight).where(
        Insight.company_id == company_id,
        Insight.deleted_at == None
    )
    
    if unread_only:
        query = query.where(Insight.is_read == False)
    
    if severity:
        query = query.where(Insight.severity == severity)
    
    # Count query
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total = count_result.scalar()
    
    # Data query
    query = query.offset(offset).limit(limit).order_by(Insight.created_at.desc())
    result = await session.execute(query)
    insights = result.scalars().all()
    
    return InsightsPublic(data=insights, total=total)


async def mark_insight_as_read(
    session: AsyncSession,
    insight_id: int
) -> InsightPublic:
    """Mark an insight as read"""
    query = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(query)
    insight = result.scalars().first()
    
    if not insight:
        raise NotFoundException("Insight not found")
    
    insight.is_read = True
    session.add(insight)
    await session.commit()
    await session.refresh(insight)
    
    return insight


# ===== AUTO-TAGGING =====

async def auto_tag_evaluation(
    session: AsyncSession,
    evaluation_id: int,
    analysis: EvaluationAnalysis
) -> list[EvaluationTagPublic]:
    """
    Automatically tag evaluation based on analysis content
    
    Tags based on:
    - IRD level (churn-risk, satisfied-customer)
    - CES level (complex-process, simple-process)
    - IOC level (sales-opportunity, missed-opportunity)
    - Quality checks (excellent-quality, needs-improvement)
    - Verbatims (positive-feedback, negative-feedback, critical-issue)
    """
    
    if not analysis.operative_view:
        return []
    
    try:
        operative_data = json.loads(analysis.operative_view) if isinstance(analysis.operative_view, str) else analysis.operative_view
    except:
        return []
    
    tags_to_add = []
    
    # IRD-based tags
    ird_score = operative_data.get("IRD", {}).get("score", 0)
    if ird_score > 70:
        tags_to_add.append("churn-risk")
    elif ird_score < 30:
        tags_to_add.append("satisfied-customer")
    
    # CES-based tags
    ces_score = operative_data.get("CES", {}).get("score", 0)
    if ces_score > 60:
        tags_to_add.append("complex-process")
    elif ces_score < 25:
        tags_to_add.append("simple-process")
    
    # IOC-based tags
    ioc_score = operative_data.get("IOC", {}).get("score", 0)
    if ioc_score > 70:
        tags_to_add.append("sales-success")
    elif ioc_score < 40:
        tags_to_add.append("missed-opportunity")
    
    # Quality-based tags
    calidad = operative_data.get("Calidad", {})
    quality_count = sum(1 for v in calidad.values() if v)
    if quality_count == len(calidad):
        tags_to_add.append("excellent-quality")
    elif quality_count <= len(calidad) / 2:
        tags_to_add.append("needs-improvement")
    
    # Verbatim-based tags
    verbatims = operative_data.get("Verbatims", {})
    if verbatims.get("positivos"):
        tags_to_add.append("positive-feedback")
    if verbatims.get("negativos"):
        tags_to_add.append("negative-feedback")
    if verbatims.get("criticos"):
        tags_to_add.append("critical-issue")
    
    # Get or create tags and associate with evaluation
    evaluation_tags = []
    for tag_name in tags_to_add:
        # Find or create tag
        tag_query = select(Tag).where(Tag.name == tag_name)
        tag_result = await session.execute(tag_query)
        tag = tag_result.scalars().first()
        
        if not tag:
            # Create default tag if doesn't exist
            tag = Tag(
                name=tag_name,
                category=get_tag_category(tag_name),
                color=get_tag_color(tag_name)
            )
            session.add(tag)
            await session.flush()
        
        # Create evaluation-tag association
        eval_tag = EvaluationTag(
            evaluation_id=evaluation_id,
            tag_id=tag.id,
            auto_tagged=True
        )
        session.add(eval_tag)
        evaluation_tags.append(eval_tag)
    
    await session.commit()
    
    return evaluation_tags


def get_tag_category(tag_name: str) -> str:
    """Get category for a tag name"""
    category_map = {
        "churn-risk": "issue",
        "satisfied-customer": "quality",
        "complex-process": "performance",
        "simple-process": "quality",
        "sales-success": "opportunity",
        "missed-opportunity": "issue",
        "excellent-quality": "quality",
        "needs-improvement": "issue",
        "positive-feedback": "quality",
        "negative-feedback": "issue",
        "critical-issue": "compliance"
    }
    return category_map.get(tag_name, "general")


def get_tag_color(tag_name: str) -> str:
    """Get color for a tag name"""
    color_map = {
        "churn-risk": "#ef4444",  # red
        "satisfied-customer": "#10b981",  # green
        "complex-process": "#f59e0b",  # orange
        "simple-process": "#10b981",  # green
        "sales-success": "#8b5cf6",  # purple
        "missed-opportunity": "#f59e0b",  # orange
        "excellent-quality": "#10b981",  # green
        "needs-improvement": "#f59e0b",  # orange
        "positive-feedback": "#10b981",  # green
        "negative-feedback": "#f59e0b",  # orange
        "critical-issue": "#ef4444"  # red
    }
    return color_map.get(tag_name, "#6b7280")


# ===== TREND ANALYSIS =====

async def calculate_trends_for_company(
    session: AsyncSession,
    company_id: int,
    metric_name: str,
    period: str = "weekly"
) -> list[TrendPublic]:
    """
    Calculate trends for a specific metric
    
    Supports: IOC, IRD, CES, NPS, quality_score
    """
    
    # Determine date range based on period
    end_date = datetime.now()
    if period == "daily":
        start_date = end_date - timedelta(days=30)
        interval = timedelta(days=1)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=12)
        interval = timedelta(weeks=1)
    else:  # monthly
        start_date = end_date - timedelta(days=180)
        interval = timedelta(days=30)
    
    # Query evaluations with analysis for the period
    query = (
        select(EvaluationAnalysis)
        .join(Evaluation)
        .join(Campaign)
        .where(
            Campaign.company_id == company_id,
            Evaluation.created_at >= start_date,
            Evaluation.deleted_at == None,
            EvaluationAnalysis.operative_view != None
        )
    )
    
    result = await session.execute(query)
    analyses = result.scalars().all()
    
    # Extract metric values and group by period
    # (Simplified - in production, use proper time-series bucketing)
    
    trends = []
    # This is a simplified version - production should use SQL window functions
    # For now, return empty list as this requires more complex querying
    
    return trends


async def check_alert_thresholds(
    session: AsyncSession,
    evaluation_id: int,
    analysis: EvaluationAnalysis,
    company_id: int
) -> list[InsightPublic]:
    """
    Check if analysis metrics exceed configured alert thresholds
    and generate insights/alerts
    """
    
    if not analysis.operative_view:
        return []
    
    try:
        operative_data = json.loads(analysis.operative_view) if isinstance(analysis.operative_view, str) else analysis.operative_view
    except:
        return []
    
    # Get active alert thresholds for company
    query = select(AlertThreshold).where(
        AlertThreshold.company_id == company_id,
        AlertThreshold.is_active == True
    )
    result = await session.execute(query)
    thresholds = result.scalars().all()
    
    triggered_insights = []
    
    for threshold in thresholds:
        metric_value = None
        
        # Extract metric value from operative_view
        if threshold.metric_name in ["IOC", "IRD", "CES"]:
            metric_value = operative_data.get(threshold.metric_name, {}).get("score")
        
        if metric_value is None:
            continue
        
        # Check threshold condition
        triggered = False
        if threshold.condition == "greater_than" and metric_value > threshold.threshold_value:
            triggered = True
        elif threshold.condition == "less_than" and metric_value < threshold.threshold_value:
            triggered = True
        elif threshold.condition == "equals" and metric_value == threshold.threshold_value:
            triggered = True
        elif threshold.condition == "between" and threshold.threshold_value_max:
            if threshold.threshold_value <= metric_value <= threshold.threshold_value_max:
                triggered = True
        
        if triggered:
            insight = InsightCreate(
                company_id=company_id,
                evaluation_id=evaluation_id,
                insight_type=f"{threshold.metric_name.lower()}_alert",
                severity=threshold.alert_severity,
                title=f"Alerta: {threshold.metric_name} = {metric_value}",
                description=f"El {threshold.metric_name} excede el umbral configurado ({threshold.condition} {threshold.threshold_value})",
                metrics={threshold.metric_name: metric_value},
                suggested_actions=[]
            )
            db_insight = Insight(**insight.model_dump())
            session.add(db_insight)
            triggered_insights.append(insight)
    
    if triggered_insights:
        await session.commit()
    
    return triggered_insights
