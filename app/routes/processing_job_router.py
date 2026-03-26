from fastapi import APIRouter, BackgroundTasks
from app.services.pipeline_service import process_interaction as run_pipeline

processing_job_router = APIRouter(prefix="/process", tags=["Processing"])


@processing_job_router.post("")
def process_video(video_url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_pipeline, video_url)
    return {"status": "queued"}
