from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.user_evaluation_summary_services import (
    get_company_users_evaluations,
    get_manager_summary,
    get_superadmin_summary,
    get_user_evaluation_summary,
)
from app.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_dashboard(
    request: Request,
    session: AsyncSession = Depends(get_db),
):

    match request.state.user.role:
        case 0:
            superadmin_summary = await get_superadmin_summary(session)

            return superadmin_summary

        case 1:
            company_users_evaluations = await get_company_users_evaluations(
                session, request.state.user.company_id
            )

            return company_users_evaluations

        case 2:
            manager_summary = await get_manager_summary(
                session, request.state.user.company_id
            )

            return manager_summary

        case 3:
            user_evaluation_summary = await get_user_evaluation_summary(
                session, request.state.user.id
            )

            return user_evaluation_summary
