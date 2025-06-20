from fastapi import logger
import httpx

from app.core.config import settings


# Construir URL de Cloudflare Stream
def get_video_url(uid: str) -> str:
    return f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/manifest/video.m3u8"


def get_video_url_download(uid: str) -> str:
    return f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/downloads/default.mp4"


# Obtener token de acceso para Symbl.ai
async def get_symbl_token() -> str:
    url = "https://api.symbl.ai/oauth2/token:generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "type": "application",
        "appId": settings.SYMBL_APP_ID,
        "appSecret": settings.SYMBL_APP_SECRET,
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, data=data)
        res.raise_for_status()
        return res.json()["accessToken"]


# Enviar el video a Symbl para análisis
async def send_video_to_symbl(video_uid: str):
    try:
        token = await get_symbl_token()
        url = "https://api.symbl.ai/v1/process/video/url"
        payload = {
            "url": f"https://cx-backend-production.up.railway.app/api/v1/cloudflare/proxy-video/{video_uid}",
            "name": "Análisis de Video",
            "confidenceThreshold": 0.6,
            "detectEntities": True,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            analysis_result = res.json()
            logger.info("✅ Resultado de Symbl.ai: %s", analysis_result)

    except Exception as e:
        logger.error("❌ Error al enviar video a Symbl.ai: %s", str(e))
