from fastapi import APIRouter

processing_job_router = APIRouter()

@processing_job_router.get("/health")
def health():
    return {"status": "ok"}
