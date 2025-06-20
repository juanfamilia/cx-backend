from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.services.symb_webhook_services import get_video_url, send_video_to_symbl


router = APIRouter(
    prefix="/symbl-webhook",
    tags=["Symbl Webhook"],
)


class CloudflareWebhook(BaseModel):
    uid: str
    status: str


@router.post("/")
async def webhook_stream(data: CloudflareWebhook, background_tasks: BackgroundTasks):
    if data.status != "ready":
        return {"message": "Video aún no está listo"}

    video_url = get_video_url(data.uid)
    print(f"🎥 Video listo: {video_url}")

    # Ejecutar análisis en segundo plano
    background_tasks.add_task(send_video_to_symbl, video_url)

    return {"message": "Procesando video con Symbl.ai"}
