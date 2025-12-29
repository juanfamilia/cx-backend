# shared/services/onboarding_services.py

import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.onboarding_model import OnboardingStatus

logger = logging.getLogger(__name__)
logger.info("🔥 onboarding_services.py LOADED")


class OnboardingService:

    @staticmethod
    async def ensure_exists(
        user_id: int,
        company_id: int,
        session: AsyncSession,
    ) -> None:

        print("🔥 ensure_exists BODY ENTERED", user_id)

        # 1️⃣ Verificar si ya existe
        result = await session.execute(
            select(OnboardingStatus).where(
                OnboardingStatus.user_id == user_id
            )
        )
        onboarding = result.scalar_one_or_none()

        if onboarding:
            print("🟡 onboarding ya existe", onboarding.id)
            return

        print("🟢 creando onboarding", user_id)

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

        print("✅ onboarding creado y commit hecho")
