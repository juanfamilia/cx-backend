from fastapi import APIRouter

processing_job_router = APIRouter(prefix="/processing")

@processing_job_router.post("/{interaction_id}")
def process_job(interaction_id: str):
    return {"status": "queued", "interaction_id": interaction_id}
