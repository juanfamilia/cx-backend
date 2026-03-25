from fastapi import APIRouter

router = APIRouter(prefix="/evaluation-events", tags=["Evaluation Events"])

@router.get("/")
def list_events():
    return {"message": "ok"}
