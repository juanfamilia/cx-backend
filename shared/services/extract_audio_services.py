# shared/services/extract_audio_services.py
import httpx

ANALYSIS_BASE_URL = "http://siete-analysis.railway.internal"

async def handle_stream_to_audio(file_bytes: bytes) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        files = {"file": ("audio.wav", file_bytes, "audio/wav")}
        resp = await client.post(f"{ANALYSIS_BASE_URL}/audio/extract", files=files)
        resp.raise_for_status()
        return resp.json()

