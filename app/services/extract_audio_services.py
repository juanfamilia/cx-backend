import os
import random
import tempfile
import time
import uuid

from fastapi import Depends
from moviepy import VideoFileClip
import requests
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.evaluation_analysis_model import EvaluationAnalysisBase
from app.services.evaluation_analysis_services import create_evaluation_analysis
from app.services.cloudflare_rs_services import r2_upload
from app.services.cloudflare_stream_services import (
    enable_download,
    get_download_status,
    wait_until_ready_to_stream,
)
from app.services.openai_services import audio_analysis


def download_video(url: str, ruta_destino: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(ruta_destino, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def extract_audio(video_path: str, audio_path: str):
    with VideoFileClip(video_path) as clip:
        clip.audio.write_audiofile(audio_path)


async def wait_and_download_video(
    video_uid: str, ruta_destino: str, max_retries: int = 10, base_wait: int = 5
):
    for intento in range(max_retries):
        status, url = await get_download_status(video_uid)
        print(f"🔃 Intento {intento + 1} | {status}")

        if status == "ready" and url:
            try:
                print("⏳ Descargando video...")
                download_video(url, ruta_destino)
                print("✅ Descarga completada.")
                return True, url  # ✅
            except Exception as e:
                print(f"❌ Error durante la descarga: {e}")
                return False, None

        # Backoff exponencial con jitter
        wait_time = base_wait * (2**intento) + random.uniform(0, 1)
        print(f"🔃 Reintentado en {wait_time:.2f} segundos...")
        time.sleep(wait_time)

    print("❌ Error limite de reintentos alcanzado.")
    return False, None


async def handle_stream_to_audio(video_uid: str, evaluation_id: int):
    id_archivo = str(uuid.uuid4())

    tmp_dir = tempfile.gettempdir()  # ✅ Asegura que /tmp exista

    video_path = f"{tmp_dir}/{id_archivo}.mp4"
    audio_path = f"{tmp_dir}/{id_archivo}.mp3"
    r2_key = f"audios/{id_archivo}.mp3"

    try:
        is_ready = await wait_until_ready_to_stream(video_uid)

        if not is_ready:
            print("❌ El video no está listo. Abortando proceso.")
            return None

        print("📥 Habilitando descarga del video en Cloudflare...")
        await enable_download(video_uid)

        print("⏳ Esperando a que el enlace de descarga esté listo...")
        success, download_url = await wait_and_download_video(video_uid, video_path)

        if not success:
            print("Fallo en la descarga del video.")
            return None

        print("🎧 Extrayendo audio...")
        extract_audio(video_path, audio_path)

        print("📤 Subiendo audio a R2...")
        r2_upload(archivo_local=audio_path, nombre_objetivo=r2_key)

        print("🧠 Enviando audio...")
        audio_result = audio_analysis(audio_path)

        print(f"📝 Transcripción completada:\n{audio_result}...")

        print("💾 Guardando análisis de evaluación...")
        evaluation_analysis = EvaluationAnalysisBase(
            evaluation_id=evaluation_id, analysis=audio_result
        )
        session: AsyncSession = Depends(get_db)

        await create_evaluation_analysis(session, evaluation_analysis)

        return "✅ Transcripción completada y guardada."

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        return None

    finally:
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Archivo temporal eliminado: {f}")
