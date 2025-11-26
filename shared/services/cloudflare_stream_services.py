import asyncio
import random
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


async def wait_until_ready_to_stream(
    video_uid: str, max_retries: int = 10, wait_seconds: int = 5
):
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream/{video_uid}"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        "Content-Type": "application/json",
    }

    for intento in range(max_retries):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if data.get("result", {}).get("readyToStream") is True:
                    print(f"✅ Video listo para streaming (intento {intento + 1})")
                    return True
                else:
                    print(f"⏳ Aún no está listo (intento {intento + 1})")
            except Exception as e:
                print(f"⚠️ Error al verificar estado de stream: {e}")

        wait_time = wait_seconds * (2**intento) + random.uniform(0, 1)
        await asyncio.sleep(wait_time)

    print("❌ Tiempo de espera agotado: el video no está listo para streaming.")
    return False


async def enable_download(video_uid: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream/{video_uid}/downloads"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        response.raise_for_status()


async def get_download_status(video_uid: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream/{video_uid}/downloads"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {}).get("default", {})
        return result.get("status"), result.get("url")
