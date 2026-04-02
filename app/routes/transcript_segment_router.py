"""
Transcript Segments Router
Endpoints for transcript segment operations
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, get_db
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException
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

logger = logging.getLogger(__name__)


def _scoped_company_id_for_search(request: Request, company_id_query: Optional[int]) -> int:
    """
    Non-admins: always their company_id (query param ignored).
    Role 0: company_id query or user's company; never unscoped (all tenants).
    """
    user = request.state.user
    if user.role != 0:
        if user.company_id is None:
            raise PermissionDeniedException(custom_message="search transcripts")
        return user.company_id
    effective = company_id_query or user.company_id
    if effective is None:
        raise PermissionDeniedException(
            custom_message=(
                "search transcripts: pass company_id query or use a user linked to a company"
            )
        )
    return effective


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
    company_id: Optional[int] = Query(
        None,
        description="Scope search to company (required for role 0 if user has no company_id)",
    ),
    branch_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    """
    Search transcript segments by text (keyword search)
    
    - **q**: Text to search for in transcripts
    - **company_id**: For admin (role 0), scopes results; ignored for other roles
    - **branch_id**: Optional filter by branch
    - **limit**: Maximum results to return (default 50, max 200)
    
    Returns matching segments with evaluation context
    """
    scoped_company_id = _scoped_company_id_for_search(request, company_id)

    return await search_transcripts_by_text(
        session=session,
        query_text=q,
        company_id=scoped_company_id,
        branch_id=branch_id,
        limit=limit,
    )


@router.post("/semantic-search", response_model=TranscriptSearchResponse)
async def semantic_search(
    request: Request,
    q: str,
    company_id: Optional[int] = Query(
        None,
        description="Scope search to company (required for role 0 if user has no company_id)",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """
    Semantic search across transcript segments using embeddings
    
    - **q**: Natural language query (e.g., "cliente frustrado", "buen servicio")
    - **company_id**: For admin (role 0), scopes results; ignored for other roles
    - **limit**: Maximum results to return (default 20, max 100)
    
    Returns matching segments ranked by semantic similarity
    """
    scoped_company_id = _scoped_company_id_for_search(request, company_id)

    return await semantic_search_transcripts(
        session=session,
        query_text=q,
        company_id=scoped_company_id,
        limit=limit,
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
            logger.info(
                "Embeddings generated for evaluation_id=%s count=%s",
                evaluation_id,
                count,
            )

    background_tasks.add_task(run_embeddings)
    
    return {"message": f"Embedding generation started for evaluation {evaluation_id}"}
