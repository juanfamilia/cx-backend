import json
from typing import Optional
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.evaluation_model import (
    Evaluation,
    EvaluationAnswerBase,
    EvaluationAnswerUpdate,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationUpdate,
    EvaluationsPublic,
    StatusEnum,
)
from app.services.evaluation_services import (
    change_evaluation_status,
    create_evaluation,
    get_evaluation,
    get_evaluations,
    soft_delete_evaluation,
    update_evaluation,
)
from app.services.video_services import upload_raw_video
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_all(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> EvaluationsPublic:

    match request.state.user.role:
        case 0:
            evaluations = await get_evaluations(session, offset, limit, filter, search)
        case 1:
            evaluations = await get_evaluations(
                session, offset, limit, filter, search, request.state.user.company_id
            )
        case 2:
            evaluations = await get_evaluations(
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.company_id,
            )
        case 3:
            evaluations = await get_evaluations(
                session,
                offset,
                limit,
                filter,
                search,
                request.state.user.company_id,
                request.state.user.id,
            )

    return evaluations


@router.put("/status/{evaluation_id}")
async def change_status(
    request: Request,
    evaluation_id: int,
    status: StatusEnum = Body(...),
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="change status")

    evaluation = await change_evaluation_status(session, evaluation_id, status)

    return evaluation


@router.get("/{evaluation_id}")
async def get_one(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    evaluation = await get_evaluation(session, evaluation_id)

    if (
        request.state.user.role != 0
        and evaluation.campaign.company_id != request.state.user.company_id
    ):
        raise PermissionDeniedException(custom_message="retrieve this evaluation")

    return evaluation


@router.post("/")
async def create(
    request: Request,
    session: AsyncSession = Depends(get_db),
    media: UploadFile = File(...),
    video_title: str = Form(...),
    campaign_id: int = Form(...),
    location: Optional[str] = Form(default=None),
    evaluated_collaborator: Optional[str] = Form(default=None),
    evaluation_answers: str = Form(...),
) -> Evaluation:

    if not media.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400, detail="Solo se permiten archivos de video"
        )

    video_upload = await upload_raw_video(session, media, video_title)

    parsed_answers = json.loads(evaluation_answers)

    # Convertir cada diccionario a una instancia de EvaluationAnswerBase
    answers_list = [EvaluationAnswerBase(**item) for item in parsed_answers]

    evaluation = EvaluationCreate(
        campaigns_id=campaign_id,
        video_id=video_upload.id,
        user_id=request.state.user.id,
        location=location,
        evaluated_collaborator=evaluated_collaborator,
        evaluation_answers=answers_list,
    )

    evaluation_db = await create_evaluation(session, evaluation)

    return evaluation_db


@router.put("/{evaluation_id}")
async def update(
    request: Request,
    evaluation_id: int,
    media: Optional[UploadFile] = File(default=None),
    video_title: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    evaluated_collaborator: Optional[str] = Form(default=None),
    evaluation_answers: Optional[str] = Form(default=None),
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    db_evaluation = await get_evaluation(session, evaluation_id)

    if request.state.user.role in [1, 2, 3]:
        if db_evaluation.campaign.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="update this evaluation")

    parsed_answers = json.loads(evaluation_answers)
    answers_list = [EvaluationAnswerUpdate(**item) for item in parsed_answers]

    evaluation_update = EvaluationUpdate(
        location=location,
        evaluated_collaborator=evaluated_collaborator,
        evaluation_answers=answers_list,
    )

    if media:
        if not media.content_type.startswith("video/"):
            raise HTTPException(
                status_code=400, detail="Solo se permiten archivos de video"
            )

        video_upload = await upload_raw_video(session, media, video_title)
        evaluation_update.video_id = video_upload.id

    evaluation = await update_evaluation(session, evaluation_id, evaluation_update)

    return evaluation


@router.delete("/{evaluation_id}")
async def delete(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
):

    if request.state.user.role in [1, 2, 3]:
        db_evaluation = await get_evaluation(session, evaluation_id)
        if db_evaluation.campaign.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="delete this evaluation")

    await soft_delete_evaluation(session, evaluation_id)

    return {"message": "Evaluation deleted"}
