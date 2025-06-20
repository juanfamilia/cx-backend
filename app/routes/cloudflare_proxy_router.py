from fastapi import APIRouter, HTTPException
import os
import tempfile

from fastapi.responses import FileResponse, StreamingResponse
import httpx

from app.services.symb_webhook_services import get_video_url


router = APIRouter(
    prefix="/cloudflare",
    tags=["Cloudflare"],
)


@router.get("/proxy-video/{video_uid}")
async def proxy_download(video_uid: str):
    url = get_video_url(video_uid)
    print(url)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="No se pudo descargar el video",
                    )

                return StreamingResponse(response.aiter_bytes(), media_type="video/mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
