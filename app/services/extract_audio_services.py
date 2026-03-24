import asyncio
import json
import os
import random
import re
import tempfile
import time
import uuid

import httpx
from moviepy import VideoFileClip
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool

from app.core.db import get_db
from app.models.evaluation_analysis_model import EvaluationAnalysisBase
from app.services.evaluation_analysis_services import (
    create_evaluation_analysis,
    split_analysis,
)
from app.services.evaluation_event_services import (
    create_events_batch,
    delete_events_for_evaluation,
    detect_events_from_segments,
)
from app.services.cloudflare_rs_services import r2_upload
from app.services.cloudflare_stream_services import (
    enable_download,
    get_download_status,
    wait_until_ready_to_stream,
)
from app.services.openai_services import audio_analysis
from app.services.transcript_segment_services import create_transcript_segments


async def download_video(url: str, ruta_destino: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(ruta_destino, "wb") as f:
                async for chunk in response.aiter_bytes():
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
                await download_video(url, ruta_destino)
                print("✅ Descarga completada.")
                return True, url  # ✅
            except Exception as e:
                print(f"❌ Error durante la descarga: {e}")
                return False, None

        # Backoff exponencial con jitter
        wait_time = base_wait * (2**intento) + random.uniform(0, 1)
        print(f"🔃 Reintentado en {wait_time:.2f} segundos...")
        await asyncio.sleep(wait_time)

    print("❌ Error limite de reintentos alcanzado.")
    return False, None


async def handle_stream_to_audio(
    video_uid: str, evaluation_id: int, session: AsyncSession
):
    id_archivo = str(uuid.uuid4())

    tmp_dir = tempfile.gettempdir()

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
        await run_in_threadpool(extract_audio, video_path, audio_path)

        print("📤 Subiendo audio a R2...")
        await run_in_threadpool(
            r2_upload, archivo_local=audio_path, nombre_objetivo=r2_key
        )

        print("🧠 Enviando audio para análisis...")
        audio_result, segments, full_transcript = await run_in_threadpool(audio_analysis, audio_path)

        print(f"📝 Transcripción completada. {len(segments)} segmentos detectados.")

        # Save transcript segments to database
        if segments:
            print("💾 Guardando segmentos de transcripción...")
            await create_transcript_segments(session, evaluation_id, segments)
            print(f"✅ {len(segments)} segmentos guardados.")

        print("💾 Guardando análisis de evaluación...")

        executive_view, operative_view = split_analysis(audio_result)

        evaluation_analysis = EvaluationAnalysisBase(
            evaluation_id=evaluation_id,
            analysis=audio_result,
            executive_view=executive_view,
            operative_view=operative_view,
        )

        await create_evaluation_analysis(session, evaluation_analysis)

        # Extract and update AI fields in evaluation
        await update_evaluation_ai_fields(session, evaluation_id, operative_view, len(segments))

        # Rebuild timeline events for this evaluation after each processing run
        await rebuild_timeline_events(session, evaluation_id, segments, operative_view)

        return "✅ Transcripción completada y guardada."

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Archivo temporal eliminado: {f}")


async def update_evaluation_ai_fields(
    session: AsyncSession,
    evaluation_id: int,
    operative_view: str,
    segment_count: int
):
    """
    Extract AI fields from operative view JSON and update the evaluation
    """
    from app.models.evaluation_model import Evaluation
    
    try:
        # Try to parse the operative view as JSON
        # The operative view might have markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', operative_view, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = operative_view
        
        data = json.loads(json_str)
        
        # Get the evaluation
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            print(f"⚠️ Evaluation {evaluation_id} not found for AI field update")
            return
        
        # Extract AI fields
        ai_extracted = data.get('ai_extracted', {})
        
        # Update fields
        if ai_extracted:
            evaluation.customer_emotion = ai_extracted.get('customer_emotion')
            evaluation.agent_emotion = ai_extracted.get('agent_emotion')
            evaluation.problem_resolved = ai_extracted.get('problem_resolved')
            evaluation.product_offered = ai_extracted.get('product_offered')
            evaluation.nps_inferred = ai_extracted.get('nps_inferred')
            evaluation.greeting_detected = ai_extracted.get('greeting_detected')
        
        # Extract CES and IRD scores
        ces = data.get('CES', {})
        ird = data.get('IRD', {})
        
        if ces:
            evaluation.customer_effort_score = ces.get('score')
        if ird:
            evaluation.risk_of_churn = ird.get('score')
        
        # Calculate service quality from Calidad fields
        calidad = data.get('Calidad', {})
        if calidad:
            quality_fields = ['saludo', 'identificacion', 'ofrecimiento', 'cierre', 'valor_agregado']
            quality_count = sum(1 for f in quality_fields if calidad.get(f, False))
            evaluation.service_quality_score = int((quality_count / len(quality_fields)) * 100)
        
        # Get duration from metadata if available
        metadata = data.get('metadata', {})
        if metadata and metadata.get('duracion_segundos'):
            evaluation.interaction_duration = metadata.get('duracion_segundos')
        
        session.add(evaluation)
        await session.commit()
        print(f"✅ AI fields updated for evaluation {evaluation_id}")
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Could not parse operative view as JSON: {e}")
    except Exception as e:
        print(f"⚠️ Error updating AI fields: {e}")


async def rebuild_timeline_events(
    session: AsyncSession,
    evaluation_id: int,
    segments: list[dict],
    operative_view: str,
):
    """
    Rebuild event timeline from transcript heuristics and AI JSON fields.
    """
    from app.models.evaluation_event_model import EvaluationEventCreate, EvaluationEventTypeEnum

    await delete_events_for_evaluation(session, evaluation_id)

    events: list[EvaluationEventCreate] = detect_events_from_segments(segments)

    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", operative_view, re.DOTALL)
        json_str = json_match.group(1) if json_match else operative_view
        data = json.loads(json_str)
        ai_extracted = data.get("ai_extracted", {})

        if ai_extracted.get("customer_emotion"):
            emotion = str(ai_extracted.get("customer_emotion")).lower()
            if any(term in emotion for term in ["frustr", "enoj", "molest", "angry"]):
                events.append(
                    EvaluationEventCreate(
                        event_type=EvaluationEventTypeEnum.EMOTIONAL_PEAK,
                        timestamp_seconds=0.0,
                        severity=4,
                        confidence=0.7,
                        evidence_text=f"customer_emotion={ai_extracted.get('customer_emotion')}",
                        source="ai_json",
                    )
                )

        if ai_extracted.get("problem_resolved") is True:
            events.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.RESOLUTION,
                    timestamp_seconds=0.0,
                    severity=2,
                    confidence=0.7,
                    evidence_text="ai_extracted.problem_resolved=true",
                    source="ai_json",
                )
            )

        if ai_extracted.get("product_offered") is True:
            events.append(
                EvaluationEventCreate(
                    event_type=EvaluationEventTypeEnum.SALES_SIGNAL,
                    timestamp_seconds=0.0,
                    severity=2,
                    confidence=0.7,
                    evidence_text="ai_extracted.product_offered=true",
                    source="ai_json",
                )
            )
    except json.JSONDecodeError:
        print("⚠️ Could not parse operative JSON for event extraction")
    except Exception as exc:
        print(f"⚠️ Error while creating events from operative JSON: {exc}")

    if events:
        await create_events_batch(session, evaluation_id, events)
        print(f"✅ {len(events)} eventos guardados para evaluación {evaluation_id}")
