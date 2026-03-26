from fastapi import APIRouter, BackgroundTasks
from app.services.pipeline_service import process_interaction as process_interaction_service

processing_job_router = APIRouter(prefix="/process", tags=["Processing"])


@processing_job_router.post("")
def process_interaction_endpoint(video_url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_interaction_service, video_url)
    return {"status": "queued"}
