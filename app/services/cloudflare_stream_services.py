import httpx
from app.core.config import settings


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
