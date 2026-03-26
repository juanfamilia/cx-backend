from fastapi import APIRouter
from app.services.pipeline_service import process_interaction

processing_job_router = APIRouter(prefix="/processing")

@processing_job_router.post("/{interaction_id}")
def process_job(interaction_id: str):
    result = process_interaction(interaction_id)
    return {
        "status": "processed",
        "data": result
    }
