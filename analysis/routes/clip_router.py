"""
Clip Router - Endpoints for accessing video clips
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.models.clip_model import ClipPublic, ClipsPublic, ClipStatus
from shared.utils.deps import check_company_payment_status, get_auth_user
from shared.utils.exceptions import NotFoundException, PermissionDeniedException
from analysis.services.clip_generation_services import (
    get_clips_for_evaluation,
    get_clip_by_id,
)


router = APIRouter(
    prefix="/clips",
    tags=["Clips"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation/{evaluation_id}", response_model=ClipsPublic)
async def get_evaluation_clips(
    request: Request,
    evaluation_id: int,
    delivered_only: bool = Query(default=True, description="Only return delivered clips (Top N)"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get clips for an evaluation
    
    By default returns only the Top N delivered clips.
    Set delivered_only=false to get all clips.
    """
    # TODO: Add permission check based on evaluation's company
    
    clips = await get_clips_for_evaluation(session, evaluation_id, delivered_only)
    
    delivered_count = sum(1 for c in clips if c.is_delivered)
    
    return ClipsPublic(
        data=[ClipPublic.model_validate(c) for c in clips],
        total=len(clips),
        delivered_count=delivered_count
    )


@router.get("/{clip_id}", response_model=ClipPublic)
async def get_single_clip(
    request: Request,
    clip_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Get a single clip by ID"""
    clip = await get_clip_by_id(session, clip_id)
    
    if not clip:
        raise NotFoundException("Clip not found")
    
    return ClipPublic.model_validate(clip)


@router.get("/evaluation/{evaluation_id}/status")
async def get_clips_status(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get processing status of clips for an evaluation
    
    Useful for polling during clip generation
    """
    from sqlmodel import select, func
    from shared.models.clip_model import Clip
    
    # Count by status
    query = select(
        Clip.status,
        func.count(Clip.id).label("count")
    ).where(
        Clip.evaluation_id == evaluation_id,
        Clip.deleted_at.is_(None)
    ).group_by(Clip.status)
    
    result = await session.execute(query)
    status_counts = {row.status: row.count for row in result}
    
    total = sum(status_counts.values())
    ready = status_counts.get(ClipStatus.READY, 0)
    failed = status_counts.get(ClipStatus.FAILED, 0)
    pending = status_counts.get(ClipStatus.PENDING, 0)
    processing = status_counts.get(ClipStatus.PROCESSING, 0) + status_counts.get(ClipStatus.UPLOADING, 0)
    
    return {
        "evaluation_id": evaluation_id,
        "total": total,
        "ready": ready,
        "failed": failed,
        "pending": pending,
        "processing": processing,
        "is_complete": pending == 0 and processing == 0,
        "success_rate": round(ready / total * 100, 1) if total > 0 else 0
    }
