from fastapi import APIRouter, HTTPException
import os
import tempfile

from fastapi.responses import FileResponse, StreamingResponse
import httpx

from app.services.cloudflare_stream_services import get_video_url


router = APIRouter(
    prefix="/cloudflare",
    tags=["Cloudflare"],
)


@router.get("/proxy-video/{video_uid}")
async def proxy_download(video_uid: str):
    return {"message": "Not implemented yet"}
