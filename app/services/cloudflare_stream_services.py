from fastapi import logger
import httpx
from app.core.config import settings


# Construir URL de Cloudflare Stream
def get_video_url(uid: str) -> str:
    return f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/manifest/video.m3u8"


def get_video_url_download(uid: str) -> str:
    return f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/downloads/default.mp4"


async def resolve_video_url(uid: str) -> str:
    url = get_video_url_download(uid)

    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            # HEAD evita descargar el archivo, pero sigue redirecciones
            response = await client.head(url, allow_redirects=True)
            final_url = str(response.url)

            # Verifica que haya sido redirigido
            if str(response.url) == url:
                logger.error(
                    "No se pudo resolver la URL del video, la URL final es la misma que la original."
                )

            return final_url

        except httpx.HTTPError as e:
            logger.error("Error al resolver URL del video: %s", str(e))


async def enable_download(video_uid: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream/{video_uid}"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        "Content-Type": "application/json",
    }
    data = {"allowDownload": True}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
