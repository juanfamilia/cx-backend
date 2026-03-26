from fastapi import APIRouter
from app.services.pipeline_service import process_interaction

processing_job_router = APIRouter(prefix="/processing")

@processing_job_router.post("/{interaction_id}")
import threading

def process_job(interaction_id: str):
    thread = threading.Thread(
        target=process_interaction,
        args=(interaction_id,)
    )
    thread.start()

    return {"status": "processing"}
