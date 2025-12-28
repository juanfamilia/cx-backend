from sqlalchemy.ext.asyncio import AsyncSession

class OnboardingService:

    @staticmethod
    async def ensure_exists(
        user_id: int,
        company_id: int,
        session: AsyncSession,
    ) -> None:
        """
        Garantiza que exista un estado de onboarding para el usuario.
        Por ahora no hace nada.
        """
        return
