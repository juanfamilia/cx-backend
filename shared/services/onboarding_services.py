from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.onboarding_model import OnboardingStatus


class OnboardingService:

    @staticmethod
    async def ensure_exists(
        user_id: int,
        company_id: int,  # se recibe aunque el modelo aún no lo use
        session: AsyncSession,
    ) -> None:
        print("🟢 ensure_exists CALLED", user_id)
        """
        Garantiza que exista un estado de onboarding para el usuario.
        Es idempotente: si existe, no hace nada.
        """

        # 1️⃣ Buscar onboarding existente
        result = await session.execute(
            select(OnboardingStatus).where(OnboardingStatus.user_id == user_id)
        )
        onboarding_status = result.scalar_one_or_none()

        # 2️⃣ Si ya existe, solo actualizar última interacción
        if onboarding_status:
            onboarding_status.last_interaction = datetime.utcnow()
            session.add(onboarding_status)
            await session.commit()
            return

        # 3️⃣ Si NO existe, crearlo
        onboarding_status = OnboardingStatus(
            user_id=user_id,
            steps_completed=[],
            tours_completed=[],
            progress_percentage=0,
            is_completed=False,
            started_at=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
        )

        session.add(onboarding_status)
        await session.commit()
