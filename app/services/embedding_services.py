"""
Embedding Services
Generate and search embeddings for semantic transcript search
"""
import json
import logging
import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.transcript_segment_model import (
    TranscriptSegment,
    TranscriptSearchResult,
    TranscriptSearchResponse,
)
from app.models.evaluation_model import Evaluation

logger = logging.getLogger(__name__)

# Using text-embedding-3-small for cost efficiency
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def get_openai_client():
    """Get OpenAI client lazily to avoid import-time errors"""
    from openai import OpenAI
    from app.core.config import settings
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a text using OpenAI
    Uses text-embedding-3-small for cost efficiency
    """
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


async def generate_embeddings_for_evaluation(
    session: AsyncSession,
    evaluation_id: int,
    batch_size: int = 20
) -> int:
    """
    Generate embeddings for all segments of an evaluation
    Returns count of segments updated
    """
    # Get all segments without embeddings
    query = select(TranscriptSegment).where(
        TranscriptSegment.evaluation_id == evaluation_id,
        TranscriptSegment.embedding_json.is_(None)
    )
    result = await session.execute(query)
    segments = result.scalars().all()
    
    if not segments:
        return 0
    
    count = 0
    for segment in segments:
        try:
            embedding = generate_embedding(segment.text)
            segment.embedding_json = json.dumps(embedding)
            session.add(segment)
            count += 1
            
            # Commit in batches
            if count % batch_size == 0:
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to generate embedding for segment_id=%s evaluation_id=%s",
                segment.id,
                evaluation_id,
            )
            continue
    
    await session.commit()
    return count


async def semantic_search_transcripts(
    session: AsyncSession,
    query_text: str,
    company_id: Optional[int] = None,
    limit: int = 20,
    similarity_threshold: float = 0.5
) -> TranscriptSearchResponse:
    """
    Semantic search across transcript segments
    
    Note: This is a simplified implementation that loads embeddings into memory.
    For production with large datasets, use pgvector for efficient similarity search.
    """
    from app.models.campaign_model import Campaign
    
    # Generate query embedding
    query_embedding = generate_embedding(query_text)
    
    # Build query to get segments with embeddings
    query = (
        select(TranscriptSegment, Evaluation)
        .join(Evaluation, TranscriptSegment.evaluation_id == Evaluation.id)
        .join(Campaign, Evaluation.campaigns_id == Campaign.id)
        .where(
            TranscriptSegment.embedding_json.isnot(None),
            Evaluation.deleted_at.is_(None)
        )
    )
    
    if company_id:
        query = query.where(Campaign.company_id == company_id)
    
    # Limit to recent segments for performance
    query = query.order_by(TranscriptSegment.created_at.desc()).limit(1000)
    
    result = await session.execute(query)
    rows = result.all()
    
    # Calculate similarity scores
    scored_results = []
    for segment, evaluation in rows:
        try:
            segment_embedding = json.loads(segment.embedding_json)
            similarity = cosine_similarity(query_embedding, segment_embedding)
            
            if similarity >= similarity_threshold:
                scored_results.append({
                    'segment': segment,
                    'evaluation': evaluation,
                    'similarity': similarity
                })
        except (json.JSONDecodeError, TypeError):
            continue
    
    # Sort by similarity and limit
    scored_results.sort(key=lambda x: x['similarity'], reverse=True)
    scored_results = scored_results[:limit]
    
    # Build response
    search_results = [
        TranscriptSearchResult(
            segment_id=r['segment'].id,
            evaluation_id=r['segment'].evaluation_id,
            start_time=r['segment'].start_time,
            end_time=r['segment'].end_time,
            text=r['segment'].text,
            branch_name=r['evaluation'].branch_name,
            interaction_date=r['evaluation'].interaction_date,
            similarity_score=round(r['similarity'], 3)
        )
        for r in scored_results
    ]
    
    return TranscriptSearchResponse(
        results=search_results,
        total=len(search_results),
        query=query_text
    )
