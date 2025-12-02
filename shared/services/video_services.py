# shared/services/video_services.py
import httpx

ANALYSIS_BASE_URL = "http://siete-analysis.railway.internal"

async def handle_video_analysis(file_bytes: bytes) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        files = {"file": ("video.mp4", file_bytes, "video/mp4")}
        resp = await client.post(f"{ANALYSIS_BASE_URL}/video/analyze", files=files)
        resp.raise_for_status()
        return resp.json()
