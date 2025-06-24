import os
import uuid
import boto3
from fastapi import logger
from moviepy import VideoFileClip
import requests

from app.core.config import settings


def download_video(url: str, ruta_destino: str):
    response = requests.get(url, stream=True)
    with open(ruta_destino, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def extract_audio(video_path: str, audio_path: str):
    with VideoFileClip(video_path) as clip:
        clip.audio.write_audiofile(audio_path)


def r2_upload(archivo_local, nombre_objetivo):
    session = boto3.Session()
    s3 = session.client(
        service_name="s3",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        endpoint_url=settings.R2_ENDPOINT_URL,
    )
    with open(archivo_local, "rb") as data:
        s3.upload_fileobj(data, settings.R2_BUCKET, nombre_objetivo)


def process_audio(video_url: str):
    try:
        id_archivo = str(uuid.uuid4())
        video_path = f"/tmp/{id_archivo}.mp4"
        audio_path = f"/tmp/{id_archivo}.mp3"

        download_video(video_url, video_path)
        extract_audio(video_path, audio_path)

        r2_upload(
            archivo_local=audio_path,
            nombre_objetivo=f"audios/{id_archivo}.mp3",
        )
        return logger.info(f"Audio procesado y subido: audios/{id_archivo}.mp3")

    except Exception as e:
        logger.error(f"Error al procesar el audio: {e}")
        return None

    finally:
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)
