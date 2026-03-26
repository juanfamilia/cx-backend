from fastapi import APIRouter, BackgroundTasks

processing_job_router = APIRouter()

@processing_job_router.post("/process")
def process_interaction(background_tasks: BackgroundTasks, video_url: str):
    background_tasks.add_task(run_pipeline, video_url)
    return {"status": "queued"}
