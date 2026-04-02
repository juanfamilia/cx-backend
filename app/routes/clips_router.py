from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.utils.deps import check_company_payment_status, get_auth_user


class ClipPublic(BaseModel):
    id: int
    evaluation_id: int
    cloudflare_uid: str | None = None
    stream_url: str | None = None
    thumbnail_url: str | None = None
    verbatim_type: Literal["critical", "negative", "positive"] = "positive"
    verbatim_text: str = ""
    verbatim_origin: str = "cliente"
    original_timestamp: int = 0
    clip_start: int = 0
    clip_end: int = 0
    clip_duration: int = 0
    priority_score: int = 0
    priority_rank: int | None = None
    is_delivered: bool = False
    status: Literal["pending", "processing", "uploading", "ready", "failed", "deleted"] = "ready"
    error_message: str | None = None
    extra_data: dict | None = None
    created_at: str = ""
    updated_at: str = ""


class ClipsResponse(BaseModel):
    data: list[ClipPublic]
    total: int
    delivered_count: int


class ClipsStatus(BaseModel):
    evaluation_id: int
    total: int
    ready: int
    failed: int
    pending: int
    processing: int
    is_complete: bool
    success_rate: float


router = APIRouter(
    prefix="/clips",
    tags=["Clips"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation/{evaluation_id}", response_model=ClipsResponse)
async def get_clips_for_evaluation(
    request: Request,
    evaluation_id: int,
    delivered_only: bool = Query(default=True),
):
    # Compatibility endpoint: returns empty set until clip pipeline is enabled.
    _ = request.state.user.company_id
    _ = delivered_only
    return ClipsResponse(data=[], total=0, delivered_count=0)


@router.get("/evaluation/{evaluation_id}/status", response_model=ClipsStatus)
async def get_clips_status(request: Request, evaluation_id: int):
    _ = request.state.user.company_id
    return ClipsStatus(
        evaluation_id=evaluation_id,
        total=0,
        ready=0,
        failed=0,
        pending=0,
        processing=0,
        is_complete=True,
        success_rate=0,
    )


@router.get("/{clip_id}", response_model=ClipPublic)
async def get_clip(request: Request, clip_id: int):
    _ = request.state.user.company_id
    # Return a neutral placeholder to avoid hard failure in viewers.
    return ClipPublic(
        id=clip_id,
        evaluation_id=0,
        created_at="",
        updated_at="",
    )
