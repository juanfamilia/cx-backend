from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db


from shared.services.campaign_assignment_services import (
    get_assiments_campaigns,
)
from shared.utils.deps import check_company_payment_status, get_auth_user
from shared.utils.exceptions import PermissionDeniedException


router = APIRouter(
    prefix="/campaign-assignment",
    tags=["Campaign Assigments"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_assiments(request: Request, session: AsyncSession = Depends(get_db)):

    if request.state.user.role != 3:
        raise PermissionDeniedException(custom_message="retrieve campaigns")

    return await get_assiments_campaigns(session, request.state.user.id)
