"""
Transcript Segment Services
Handles storage and retrieval of transcript segments
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, or_

from app.models.transcript_segment_model import (
    TranscriptSegment,
    TranscriptSegmentCreate,
    TranscriptSegmentPublic,
    TranscriptSegmentsPublic,
    TranscriptSearchResult,
    TranscriptSearchResponse,
)
from app.models.evaluation_model import Evaluation
from app.utils.exeptions import NotFoundException


async def create_transcript_segments(
    session: AsyncSession,
    evaluation_id: int,
    segments: List[dict]
) -> List[TranscriptSegment]:
    """
    Create transcript segments from Whisper response
    
    Args:
        session: Database session
        evaluation_id: ID of the evaluation
        segments: List of segment dicts from Whisper verbose_json
                 Each has: start, end, text, (optionally: avg_logprob)
    """
    db_segments = []
    
    for seg in segments:
        # Extract confidence if available (from avg_logprob)
        confidence = None
        if 'avg_logprob' in seg:
            # Convert log probability to confidence (0-1)
            import math
            confidence = math.exp(seg['avg_logprob'])
        
        db_segment = TranscriptSegment(
            evaluation_id=evaluation_id,
            start_time=seg["start"],
            end_time=seg["end"],
            text=seg["text"].strip(),
            confidence=confidence,
            speaker=seg.get("speaker"),
        )
        session.add(db_segment)
        db_segments.append(db_segment)
    
    await session.commit()
    
    # Refresh all to get IDs
    for seg in db_segments:
        await session.refresh(seg)
    
    return db_segments


async def get_segments_for_evaluation(
    session: AsyncSession,
    evaluation_id: int
) -> TranscriptSegmentsPublic:
    """Get all transcript segments for an evaluation, ordered by time"""
    query = select(TranscriptSegment).where(
        TranscriptSegment.evaluation_id == evaluation_id
    ).order_by(TranscriptSegment.start_time)
    
    result = await session.execute(query)
    segments = result.scalars().all()
    
    if not segments:
        return TranscriptSegmentsPublic(data=[], total=0, duration=0.0)
    
    # Calculate total duration from last segment
    duration = segments[-1].end_time if segments else 0.0
    
    return TranscriptSegmentsPublic(
        data=[TranscriptSegmentPublic.model_validate(s) for s in segments],
        total=len(segments),
        duration=duration
    )


async def search_transcripts_by_text(
    session: AsyncSession,
    query_text: str,
    company_id: Optional[int] = None,
    branch_id: Optional[str] = None,
    limit: int = 50
) -> TranscriptSearchResponse:
    """
    Search transcript segments by text (keyword search)
    
    Args:
        session: Database session
        query_text: Text to search for
        company_id: Optional filter by company
        branch_id: Optional filter by branch
        limit: Maximum results to return
    """
    from app.models.campaign_model import Campaign
    
    # Build query with joins to get evaluation context
    query = (
        select(TranscriptSegment, Evaluation)
        .join(Evaluation, TranscriptSegment.evaluation_id == Evaluation.id)
        .join(Campaign, Evaluation.campaigns_id == Campaign.id)
        .where(
            TranscriptSegment.text.ilike(f"%{query_text}%"),
            Evaluation.deleted_at.is_(None)
        )
    )
    
    if company_id:
        query = query.where(Campaign.company_id == company_id)
    
    if branch_id:
        query = query.where(Evaluation.branch_id == branch_id)
    
    query = query.order_by(TranscriptSegment.created_at.desc()).limit(limit)
    
    result = await session.execute(query)
    rows = result.all()
    
    search_results = []
    for segment, evaluation in rows:
        search_results.append(TranscriptSearchResult(
            segment_id=segment.id,
            evaluation_id=segment.evaluation_id,
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=segment.text,
            branch_name=evaluation.branch_name,
            interaction_date=evaluation.interaction_date,
        ))
    
    return TranscriptSearchResponse(
        results=search_results,
        total=len(search_results),
        query=query_text
    )


async def get_segment_by_id(
    session: AsyncSession,
    segment_id: int
) -> TranscriptSegment:
    """Get a single segment by ID"""
    segment = await session.get(TranscriptSegment, segment_id)
    if not segment:
        raise NotFoundException("Transcript segment not found")
    return segment


async def delete_segments_for_evaluation(
    session: AsyncSession,
    evaluation_id: int
) -> int:
    """Delete all segments for an evaluation (used when re-processing)"""
    from sqlmodel import delete
    
    stmt = delete(TranscriptSegment).where(
        TranscriptSegment.evaluation_id == evaluation_id
    )
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount
