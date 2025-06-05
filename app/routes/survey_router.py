from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.survey_forms_model import (
    SurveyForm,
    SurveyFormPublic,
    SurveyFormsCreate,
    SurveyFormsPublic,
)
from app.models.survey_model import SurveySectionPublic
from app.services.survey_forms_services import (
    create_survey_form,
    get_form_by_id,
    get_forms_by_company,
    soft_delete_form,
    update_survey_form,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/survey",
    tags=["Survey"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/forms")
async def get_all_forms(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> SurveyFormsPublic:

    if request.state.user.role not in [0, 1, 2]:
        raise PermissionDeniedException(custom_message="retrieve forms")

    surveyForms = await get_forms_by_company(
        session, request.state.user.company_id, offset, limit, filter, search
    )

    return surveyForms


@router.get("/forms/{form_id}")
async def get_one_form(
    form_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> SurveyFormPublic:

    surveyForm = await get_form_by_id(session, form_id, request.state.user.company_id)

    return surveyForm


@router.post("/forms")
async def create_form(
    request: Request,
    data: SurveyFormsCreate,
    session: AsyncSession = Depends(get_db),
) -> SurveyForm:

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="create a survey form")

    surveyForm = await create_survey_form(session, request.state.user.company_id, data)

    return surveyForm


@router.put("/forms/{form_id}")
async def update_form(
    form_id: int,
    data: SurveyFormsCreate,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> SurveyForm:

    if request.state.user.role != 1:
        raise PermissionDeniedException(custom_message="update a survey form")

    surveyForm = await update_survey_form(
        session, form_id, request.state.user.company_id, data
    )

    return surveyForm


@router.delete("/forms/{form_id}")
async def delete_form(
    form_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    await soft_delete_form(session, form_id, request.state.user.company_id)

    return {"message": "Survey form deleted"}
