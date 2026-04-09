from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation_analysis_model import EvaluationAnalysis
from app.models.transcript_segment_model import TranscriptSegment
from app.types.evaluation_ai_processing import EvaluationAiProcessingPublic


async def get_evaluation_ai_processing(
    session: AsyncSession, evaluation_id: int
) -> EvaluationAiProcessingPublic:
    seg_count = (
        await session.execute(
            select(func.count(TranscriptSegment.id)).where(
                TranscriptSegment.evaluation_id == evaluation_id
            )
        )
    ).scalar_one()
    transcript_segment_count = int(seg_count or 0)

    analysis_row = (
        await session.execute(
            select(EvaluationAnalysis.id).where(
                EvaluationAnalysis.evaluation_id == evaluation_id,
                EvaluationAnalysis.deleted_at == None,
            ).limit(1)
        )
    ).first()
    has_analysis = analysis_row is not None

    if has_analysis:
        return EvaluationAiProcessingPublic(
            evaluation_id=evaluation_id,
            transcript_segment_count=transcript_segment_count,
            has_analysis=True,
            status="complete",
            user_message_es="El análisis IA está disponible.",
            hint="READY",
        )

    if transcript_segment_count == 0:
        return EvaluationAiProcessingPublic(
            evaluation_id=evaluation_id,
            transcript_segment_count=0,
            has_analysis=False,
            status="pending",
            user_message_es=(
                "El procesamiento de audio e IA aún no ha terminado o no ha comenzado. "
                "Espere unos minutos y pulse Reintentar."
            ),
            hint="WAIT_FOR_PIPELINE",
        )

    return EvaluationAiProcessingPublic(
        evaluation_id=evaluation_id,
        transcript_segment_count=transcript_segment_count,
        has_analysis=False,
        status="transcript_only",
        user_message_es=(
            "La transcripción está lista, pero el análisis IA no se generó. "
            "Puede revisar la pestaña de video y transcripción o intentar más tarde."
        ),
        hint="TRANSCRIPT_WITHOUT_ANALYSIS",
    )
