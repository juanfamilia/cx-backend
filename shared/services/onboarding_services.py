# shared/services/onboarding_services.py

import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.onboarding_model import OnboardingStatus

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Servicio responsable del ciclo de vida del onboarding:
    - Garantizar existencia
    - Registrar progreso
    - Marcar finalización
    """

    # ─────────────────────────────
    # CREACIÓN / GARANTÍA DE ESTADO
    # ─────────────────────────────
    @staticmethod
    async def ensure_exists(
        user_id: int,
        company_id: int,
        session: AsyncSession,
    ) -> None:
        result = await session.execute(
            select(OnboardingStatus).where(
                OnboardingStatus.user_id == user_id
            )
        )
        onboarding = result.scalar_one_or_none()

        if onboarding:
            logger.debug(
                "Onboarding ya existe | user_id=%s onboarding_id=%s",
                user_id,
                onboarding.id,
            )
            return

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

        logger.info(
            "Onboarding creado | user_id=%s company_id=%s",
            user_id,
            company_id,
        )

    # ─────────────────────────────
    # REGISTRO DE TOURS
    # ─────────────────────────────
    @staticmethod
    async def complete_tour(
        user_id: int,
        tour: str,
        completion_type: str,  # completed | skipped
        session: AsyncSession,
    ) -> None:
        onboarding = await session.get(OnboardingStatus, user_id)

        if not onboarding:
            logger.warning(
                "complete_tour sin onboarding | user_id=%s tour=%s",
                user_id,
                tour,
            )
            return

        if tour not in onboarding.tours_completed:
            onboarding.tours_completed.append(tour)

        onboarding.last_interaction = datetime.utcnow()

        logger.info(
            "Tour registrado | user_id=%s tour=%s type=%s",
            user_id,
            tour,
            completion_type,
        )

        await OnboardingService._recalculate_progress(onboarding)
        await session.commit()

    # ─────────────────────────────
    # REGISTRO DE STEPS (OPCIONAL)
    # ─────────────────────────────
    @staticmethod
    async def complete_step(
        user_id: int,
        step: str,
        session: AsyncSession,
    ) -> None:
        onboarding = await session.get(OnboardingStatus, user_id)

        if not onboarding:
            return

        if step not in onboarding.steps_completed:
            onboarding.steps_completed.append(step)

        onboarding.last_interaction = datetime.utcnow()

        await OnboardingService._recalculate_progress(onboarding)
        await session.commit()

    # ─────────────────────────────
    # CÁLCULO DE PROGRESO
    # ─────────────────────────────
    @staticmethod
    async def _recalculate_progress(onboarding: OnboardingStatus) -> None:
        """
        Regla simple (ajustable):
        - Cada tour vale lo mismo
        - Si todos los tours definidos están completos → onboarding completo
        """

        EXPECTED_TOURS = {
            "welcome",
            "dashboard",
            "analytics",
            "calls",
        }

        completed = set(onboarding.tours_completed or [])
        total = len(EXPECTED_TOURS)

        if total == 0:
            onboarding.progress_percentage = 100
            onboarding.is_completed = True
            return

        progress = int((len(completed & EXPECTED_TOURS) / total) * 100)
        onboarding.progress_percentage = progress

        if progress >= 100:
            onboarding.is_completed = True
            logger.info(
                "Onboarding completado | user_id=%s",
                onboarding.user_id,
            )
