from fastapi import APIRouter
from pydantic import BaseModel

from app.services.cloudflare_stream_services import get_video_url


router = APIRouter(
    prefix="/cloudflare-webhook",
    tags=["Cloudflare Webhook"],
)


class CloudflareWebhook(BaseModel):
    uid: str
    status: str


@router.post("/")
async def webhook_stream():
    return {"message": "Not implemented yet"}
