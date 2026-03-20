"""
Transcript Segments Router
Endpoints for transcript segment operations
"""
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.utils.deps import get_auth_user
from app.models.user_model import UserPublic
from app.models.transcript_segment_model import (
    TranscriptSegmentsPublic,
    TranscriptSearchResponse,
)
from app.services.transcript_segment_services import (
    get_segments_for_evaluation,
    search_transcripts_by_text,
)
from app.services.embedding_services import (
    generate_embeddings_for_evaluation,
    semantic_search_transcripts,
)


router = APIRouter(
    prefix="/transcript-segments",
    tags=["Transcript Segments"],
)


@router.get("/evaluation/{evaluation_id}", response_model=TranscriptSegmentsPublic)
async def get_evaluation_transcript(
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_auth_user),
):
    """
    Get all transcript segments for an evaluation
    Returns segments ordered by start time for synchronized playback
    """
    return await get_segments_for_evaluation(session, evaluation_id)


@router.get("/search", response_model=TranscriptSearchResponse)
async def search_transcripts(
    q: str,
    branch_id: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_auth_user),
):
    """
    Search transcript segments by text (keyword search)
    
    - **q**: Text to search for in transcripts
    - **branch_id**: Optional filter by branch
    - **limit**: Maximum results to return (default 50)
    
    Returns matching segments with evaluation context
    """
    # Get company_id from current user
    company_id = current_user.company_id if hasattr(current_user, 'company_id') else None
    
    return await search_transcripts_by_text(
        session=session,
        query_text=q,
        company_id=company_id,
        branch_id=branch_id,
        limit=limit
    )


@router.post("/semantic-search", response_model=TranscriptSearchResponse)
async def semantic_search(
    q: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_auth_user),
):
    """
    Semantic search across transcript segments using embeddings
    
    - **q**: Natural language query (e.g., "cliente frustrado", "buen servicio")
    - **limit**: Maximum results to return (default 20)
    
    Returns matching segments ranked by semantic similarity
    """
    company_id = current_user.company_id if hasattr(current_user, 'company_id') else None
    
    return await semantic_search_transcripts(
        session=session,
        query_text=q,
        company_id=company_id,
        limit=limit
    )


@router.post("/evaluation/{evaluation_id}/generate-embeddings")
async def generate_evaluation_embeddings(
    evaluation_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_auth_user),
):
    """
    Generate embeddings for all segments of an evaluation
    This enables semantic search for this evaluation's transcript
    
    Runs in background for large transcripts
    """
    # Run embedding generation in background
    async def run_embeddings():
        count = await generate_embeddings_for_evaluation(session, evaluation_id)
        print(f"Generated {count} embeddings for evaluation {evaluation_id}")
    
    background_tasks.add_task(run_embeddings)
    
    return {"message": f"Embedding generation started for evaluation {evaluation_id}"}
