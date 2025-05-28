from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.survey_model import SurveySection, SurveySectionPublic
from app.services.survey_services import get_survey
from app.utils.deps import check_company_payment_status, get_auth_user


router = APIRouter(
    prefix="/survey",
    tags=["Survey"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/", response_model=List[SurveySectionPublic])
async def get_all(session: AsyncSession = Depends(get_db)) -> List[SurveySection]:

    survey = await get_survey(session)

    return survey


@router.post("/")
async def create(
    video: UploadFile = File(...),
    video_title: str = Form(...),
    user_id: str = Form(...),
    evaluation_type: str = Form(...),
    location: str = Form(...),
    evaluated_collaborator: str = Form(None),
    answers: str = Form(...),
    session: AsyncSession = Depends(get_db),
):
    pass
