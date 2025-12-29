from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models.onboarding_model import OnboardingStatus


class OnboardingService:

    @staticmethod
    async def ensure_exists(
        user_id: int,
        company_id: int,
        session: AsyncSession,
    ) -> None:
        # 1️⃣ Verificar si ya existe
        result = await session.execute(
            select(OnboardingStatus).where(
                OnboardingStatus.user_id == user_id
            )
        )
        onboarding = result.scalar_one_or_none()

        if onboarding:
            return  # ya existe, no hacer nada

        # 2️⃣ Crear registro inicial
        onboarding = OnboardingStatus(
            user_id=user_id,
            company_id=company_id,
            steps_completed=[],
            tours_completed=[],
            progress_percentage=0,
            is_completed=False,
            started_at=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
        )

        session.add(onboarding)
        await session.commit()
