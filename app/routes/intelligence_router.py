from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.utils.deps import check_company_payment_status, get_auth_user


class InsightPublic(BaseModel):
    id: int
    company_id: int
    evaluation_id: int | None = None
    title: str
    description: str
    insight_type: str = "trend"
    severity: Literal["critical", "high", "medium", "low"] = "low"
    confidence_score: float = 0
    suggested_actions: list[str] = []
    is_read: bool = False
    created_at: str
    updated_at: str


class InsightsPublic(BaseModel):
    data: list[InsightPublic]
    total: int


class InsightSummary(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    total_unread: int


class TrendDataset(BaseModel):
    label: str
    data: list[int]


class InsightTrends(BaseModel):
    labels: list[str]
    datasets: list[TrendDataset]


class TopAction(BaseModel):
    action: str
    frequency: int


class TopActionsResponse(BaseModel):
    top_actions: list[TopAction]


_INSIGHTS_BY_COMPANY: dict[int, list[InsightPublic]] = {}


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/insights", response_model=InsightsPublic)
async def get_insights(
    request: Request,
    offset: int = 0,
    limit: int = Query(default=50, le=200),
    severity: str | None = None,
    unread_only: bool | None = None,
):
    company_id = request.state.user.company_id
    data = list(_INSIGHTS_BY_COMPANY.get(company_id, []))
    if severity:
        data = [x for x in data if x.severity == severity]
    if unread_only:
        data = [x for x in data if not x.is_read]
    total = len(data)
    return InsightsPublic(data=data[offset : offset + limit], total=total)


@router.get("/insights/summary", response_model=InsightSummary)
async def get_insights_summary(request: Request):
    company_id = request.state.user.company_id
    data = _INSIGHTS_BY_COMPANY.get(company_id, [])
    return InsightSummary(
        critical=sum(1 for x in data if x.severity == "critical"),
        high=sum(1 for x in data if x.severity == "high"),
        medium=sum(1 for x in data if x.severity == "medium"),
        low=sum(1 for x in data if x.severity == "low"),
        total_unread=sum(1 for x in data if not x.is_read),
    )


@router.get("/insights/trends", response_model=InsightTrends)
async def get_insights_trends(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
):
    _ = request.state.user.company_id
    _ = days
    return InsightTrends(
        labels=[],
        datasets=[
            TrendDataset(label="critical", data=[]),
            TrendDataset(label="high", data=[]),
            TrendDataset(label="medium", data=[]),
            TrendDataset(label="low", data=[]),
        ],
    )


@router.get("/insights/top-actions", response_model=TopActionsResponse)
async def get_top_actions(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
):
    _ = request.state.user.company_id
    _ = limit
    return TopActionsResponse(top_actions=[])


@router.put("/insights/{insight_id}/read", response_model=InsightPublic)
async def mark_insight_as_read(request: Request, insight_id: int):
    company_id = request.state.user.company_id
    insights = _INSIGHTS_BY_COMPANY.get(company_id, [])
    for idx, item in enumerate(insights):
        if item.id == insight_id:
            updated = item.model_copy(update={"is_read": True, "updated_at": _now_iso()})
            insights[idx] = updated
            return updated

    now = _now_iso()
    placeholder = InsightPublic(
        id=insight_id,
        company_id=company_id,
        title="Insight",
        description="Insight placeholder",
        is_read=True,
        created_at=now,
        updated_at=now,
    )
    insights.append(placeholder)
    _INSIGHTS_BY_COMPANY[company_id] = insights
    return placeholder
