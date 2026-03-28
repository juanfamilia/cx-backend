"""
Transcript Segments Router
Endpoints for transcript segment operations
"""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, get_db
from app.utils.deps import check_company_payment_status, get_auth_user
from app.services.evaluation_services import assert_evaluation_access
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
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/evaluation/{evaluation_id}", response_model=TranscriptSegmentsPublic)
async def get_evaluation_transcript(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    Get all transcript segments for an evaluation
    Returns segments ordered by start time for synchronized playback
    """
    await assert_evaluation_access(session, evaluation_id, request.state.user)
    return await get_segments_for_evaluation(session, evaluation_id)


@router.get("/search", response_model=TranscriptSearchResponse)
async def search_transcripts(
    request: Request,
    q: str,
    branch_id: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
):
    """
    Search transcript segments by text (keyword search)
    
    - **q**: Text to search for in transcripts
    - **branch_id**: Optional filter by branch
    - **limit**: Maximum results to return (default 50)
    
    Returns matching segments with evaluation context
    """
    company_id = request.state.user.company_id

    return await search_transcripts_by_text(
        session=session,
        query_text=q,
        company_id=company_id,
        branch_id=branch_id,
        limit=limit
    )


@router.post("/semantic-search", response_model=TranscriptSearchResponse)
async def semantic_search(
    request: Request,
    q: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
):
    """
    Semantic search across transcript segments using embeddings
    
    - **q**: Natural language query (e.g., "cliente frustrado", "buen servicio")
    - **limit**: Maximum results to return (default 20)
    
    Returns matching segments ranked by semantic similarity
    """
    company_id = request.state.user.company_id

    return await semantic_search_transcripts(
        session=session,
        query_text=q,
        company_id=company_id,
        limit=limit
    )


@router.post("/evaluation/{evaluation_id}/generate-embeddings")
async def generate_evaluation_embeddings(
    request: Request,
    evaluation_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Generate embeddings for all segments of an evaluation
    This enables semantic search for this evaluation's transcript
    
    Runs in background for large transcripts
    """
    await assert_evaluation_access(session, evaluation_id, request.state.user)

    async def run_embeddings():
        async with AsyncSessionLocal() as bg_session:
            count = await generate_embeddings_for_evaluation(
                bg_session, evaluation_id
            )
            print(f"Generated {count} embeddings for evaluation {evaluation_id}")

    background_tasks.add_task(run_embeddings)
    
    return {"message": f"Embedding generation started for evaluation {evaluation_id}"}
