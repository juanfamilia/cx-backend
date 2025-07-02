from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.evaluation_analysis_model import (
    EvaluationAnalysis,
    EvaluationAnalysisBase,
    EvaluationAnalysisPublic,
)
from app.utils.exeptions import NotFoundException


async def get_evaluation_analysis(
    session: AsyncSession, evaluation_id: int
) -> EvaluationAnalysisPublic:

    query = select(EvaluationAnalysis).where(
        EvaluationAnalysis.evaluation_id == evaluation_id,
        EvaluationAnalysis.deleted_at == None,
    )

    result = await session.execute(query)
    db_evaluation_analysis = result.scalars().first()

    if not db_evaluation_analysis:
        raise NotFoundException("Evaluation analysis not found")

    return db_evaluation_analysis


async def create_evaluation_analysis(
    session: AsyncSession, evaluation_analysis: EvaluationAnalysisBase
) -> EvaluationAnalysisPublic:
    db_evaluation_analysis = EvaluationAnalysis(**evaluation_analysis.model_dump())

    session.add(db_evaluation_analysis)
    await session.commit()
    await session.refresh(db_evaluation_analysis)

    return db_evaluation_analysis


async def soft_delete_evaluation_analysis(
    session: AsyncSession, evaluation_analysis_id: int
) -> EvaluationAnalysisPublic:
    db_evaluation_analysis = await get_evaluation_analysis(
        session, evaluation_analysis_id
    )

    db_evaluation_analysis.deleted_at = datetime.now()

    session.add(db_evaluation_analysis)
    await session.commit()
    await session.refresh(db_evaluation_analysis)

    return db_evaluation_analysis
