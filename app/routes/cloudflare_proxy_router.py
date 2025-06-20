from fastapi import APIRouter, HTTPException, Response
import httpx

from app.services.symb_webhook_services import get_video_url


router = APIRouter(
    prefix="/cloudflare",
    tags=["Cloudflare"],
)


@router.get("/proxy-video/{video_uid}")
async def proxy_video(video_uid: str):
    download_url = get_video_url(video_uid)

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        try:
            # Realiza la petición al enlace de descarga de Cloudflare
            async with client.stream("GET", download_url) as resp:
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail="No se pudo obtener el video",
                    )

                headers = {
                    "Content-Type": resp.headers.get("Content-Type", "video/mp4"),
                    "Content-Length": resp.headers.get("Content-Length", None),
                }

                # Retorna un streaming directo al cliente
                return Response(content=await resp.aread(), headers=headers)
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"Error al acceder al video: {str(e)}"
            )
