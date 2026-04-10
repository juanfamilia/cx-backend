import json
from typing import List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    Query,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.db import AsyncSessionLocal, get_db
from app.models.evaluation_model import (
    EvaluationAnswerBase,
    EvaluationAnswerUpdate,
    EvaluationCreate,
    EvaluationPublic,
    EvaluationUpdate,
    EvaluationsPublic,
    StatusChangeRequest,
    StatusEnum,
)
from app.models.video_model import Video
from app.services.cloudflare_stream_services import get_video_url
from app.services.evaluation_services import (
    change_evaluation_status,
    create_evaluation,
    get_evaluation,
    get_evaluations,
    soft_delete_evaluation,
    update_evaluation,
)
from app.services.evaluation_ai_processing_service import (
    get_evaluation_ai_processing,
)
from app.services.extract_audio_services import handle_stream_to_audio
from app.services.video_services import (
    create_video,
    update_video_status,
)
from app.types.evaluation_ai_processing import EvaluationAiProcessingPublic
from app.services.audit_services import log_change
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


def _parse_visited_zones_json(raw: Optional[str]) -> List[int]:
    """Parse JSON array from form field (same format as the Angular client)."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return []
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return [int(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


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
    status: StatusChangeRequest = Body(...),
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    if request.state.user.role not in [1, 2]:
        raise PermissionDeniedException(custom_message="change status")

    prev = await get_evaluation(session, evaluation_id)
    prev_status = prev.status

    evaluation = await change_evaluation_status(session, evaluation_id, status)

    await log_change(
        session,
        user_id=request.state.user.id,
        user_email=request.state.user.email,
        entity_type="evaluations",
        entity_id=evaluation_id,
        action="status_change",
        field_name="status",
        old_value=prev_status,
        new_value=status.status,
        justification=status.comment,
    )

    return evaluation


@router.get("/check-video/{video_id}")
async def check_video(
    request: Request,
    video_id: int,
    session: AsyncSession = Depends(get_db),
) -> Video:

    video = await update_video_status(session, video_id)

    return video


@router.get(
    "/{evaluation_id}/ai-processing",
    response_model=EvaluationAiProcessingPublic,
)
async def get_ai_processing(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> EvaluationAiProcessingPublic:
    evaluation = await get_evaluation(session, evaluation_id)

    if request.state.user.role != 0 and (
        evaluation.campaign is None
        or evaluation.campaign.company_id != request.state.user.company_id
    ):
        raise PermissionDeniedException(custom_message="retrieve this evaluation")

    return await get_evaluation_ai_processing(session, evaluation_id)


@router.get("/{evaluation_id}")
async def get_one(
    request: Request,
    evaluation_id: int,
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    evaluation = await get_evaluation(session, evaluation_id)

    if request.state.user.role != 0 and (
        evaluation.campaign is None
        or evaluation.campaign.company_id != request.state.user.company_id
    ):
        raise PermissionDeniedException(custom_message="retrieve this evaluation")

    return evaluation


@router.post("/", response_model=EvaluationPublic)
async def create(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    media_url: str = Form(...),
    video_title: str = Form(...),
    campaign_id: int = Form(...),
    location: Optional[str] = Form(default=None),
    evaluated_collaborator: Optional[str] = Form(default=None),
    visited_zones: Optional[str] = Form(
        default=None,
        description="JSON array of zone ids, e.g. [1,2]",
    ),
    evaluation_answers: str = Form(...),
) -> EvaluationPublic:

    video_url = get_video_url(media_url)
    video_upload = await create_video(session, video_url, video_title)

    parsed_answers = json.loads(evaluation_answers)
    answers_list = [EvaluationAnswerBase(**item) for item in parsed_answers]

    evaluation = EvaluationCreate(
        campaigns_id=campaign_id,
        video_id=video_upload.id,
        user_id=request.state.user.id,
        location=location,
        evaluated_collaborator=evaluated_collaborator,
        visited_zones=_parse_visited_zones_json(visited_zones),
        evaluation_answers=answers_list,
    )

    evaluation_db = await create_evaluation(session, evaluation)

    async def run_audio_pipeline(video_uid: str, evaluation_id: int) -> None:
        async with AsyncSessionLocal() as bg_session:
            await handle_stream_to_audio(video_uid, evaluation_id, bg_session)

    background_tasks.add_task(run_audio_pipeline, media_url, evaluation_db.id)

    return await get_evaluation(session, evaluation_db.id)


@router.put("/{evaluation_id}")
async def update(
    request: Request,
    evaluation_id: int,
    background_tasks: BackgroundTasks,
    media_url: Optional[str] = Form(default=None),
    video_title: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    evaluated_collaborator: Optional[str] = Form(default=None),
    visited_zones: Optional[str] = Form(
        default=None,
        description="JSON array of zone ids; omit to leave unchanged",
    ),
    evaluation_answers: Optional[str] = Form(default=None),
    session: AsyncSession = Depends(get_db),
) -> EvaluationPublic:

    db_evaluation = await get_evaluation(session, evaluation_id)

    if request.state.user.role in [1, 2, 3]:
        if (
            db_evaluation.campaign is None
            or db_evaluation.campaign.company_id != request.state.user.company_id
        ):
            raise PermissionDeniedException(custom_message="update this evaluation")

    answers_list: Optional[List[EvaluationAnswerUpdate]] = None
    if evaluation_answers is not None and evaluation_answers.strip():
        parsed_answers = json.loads(evaluation_answers)
        answers_list = [EvaluationAnswerUpdate(**item) for item in parsed_answers]

    update_payload = {
        "location": location,
        "evaluated_collaborator": evaluated_collaborator,
        "evaluation_answers": answers_list,
    }
    if visited_zones is not None:
        update_payload["visited_zones"] = _parse_visited_zones_json(visited_zones)

    evaluation_update = EvaluationUpdate(**update_payload)

    if media_url:
        video_url = get_video_url(media_url)
        video_upload = await create_video(session, video_url, video_title)
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
        if (
            db_evaluation.campaign is None
            or db_evaluation.campaign.company_id != request.state.user.company_id
        ):
            raise PermissionDeniedException(custom_message="delete this evaluation")

    await soft_delete_evaluation(session, evaluation_id)

    return {"message": "Evaluation deleted"}
