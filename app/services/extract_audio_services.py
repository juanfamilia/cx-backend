import asyncio
import json
import logging
import os
import random
import re
import tempfile
import uuid

import httpx
from moviepy import VideoFileClip
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
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
    is_undefined_evaluation_events_table_error,
)
from app.services.cloudflare_rs_services import r2_upload
from app.services.cloudflare_stream_services import (
    enable_download,
    get_download_status,
    wait_until_ready_to_stream,
)
from app.services.openai_services import audio_analysis
from app.services.transcript_segment_services import create_transcript_segments

logger = logging.getLogger(__name__)


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
        logger.info("Video download attempt %s status=%s", intento + 1, status)

        if status == "ready" and url:
            try:
                logger.info("Downloading video from Cloudflare")
                await download_video(url, ruta_destino)
                logger.info("Video download completed")
                return True, url  # ✅
            except Exception as e:
                logger.warning("Video download failed: %s", e)
                return False, None

        # Backoff exponencial con jitter
        wait_time = base_wait * (2**intento) + random.uniform(0, 1)
        logger.info("Retrying download in %.2f seconds", wait_time)
        await asyncio.sleep(wait_time)

    logger.error("Video download max retries exceeded for uid=%s", video_uid)
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
            logger.warning(
                "Video not ready to stream, aborting evaluation_id=%s", evaluation_id
            )
            return None

        logger.info("Enabling Cloudflare download evaluation_id=%s", evaluation_id)
        await enable_download(video_uid)

        logger.info("Waiting for download URL evaluation_id=%s", evaluation_id)
        success, download_url = await wait_and_download_video(video_uid, video_path)

        if not success:
            logger.error("Video download failed evaluation_id=%s", evaluation_id)
            return None

        logger.info("Extracting audio evaluation_id=%s", evaluation_id)
        await run_in_threadpool(extract_audio, video_path, audio_path)

        logger.info("Uploading audio to R2 evaluation_id=%s", evaluation_id)
        await run_in_threadpool(
            r2_upload, archivo_local=audio_path, nombre_objetivo=r2_key
        )

        logger.info("Running audio analysis evaluation_id=%s", evaluation_id)
        audio_result, segments, full_transcript = await run_in_threadpool(audio_analysis, audio_path)

        logger.info(
            "Transcription done evaluation_id=%s segment_count=%s",
            evaluation_id,
            len(segments),
        )

        # Save transcript segments to database
        if segments:
            logger.info("Saving transcript segments evaluation_id=%s", evaluation_id)
            await create_transcript_segments(session, evaluation_id, segments)
            logger.info(
                "Transcript segments saved evaluation_id=%s count=%s",
                evaluation_id,
                len(segments),
            )

        if settings.DELIVERY_VIDEO_ENABLED and segments:
            from app.services.video_delivery_edit_services import (
                compose_and_upload_delivery_video,
            )

            dk = await compose_and_upload_delivery_video(
                session, evaluation_id, video_path, segments
            )
            if dk:
                logger.info(
                    "Delivery video composed evaluation_id=%s r2_key=%s",
                    evaluation_id,
                    dk,
                )

        logger.info("Saving evaluation analysis evaluation_id=%s", evaluation_id)

        executive_view, operative_view = split_analysis(audio_result)

        evaluation_analysis = EvaluationAnalysisBase(
            evaluation_id=evaluation_id,
            transcript_text=full_transcript,
            analysis=audio_result,
            executive_view=executive_view,
            operative_view=operative_view,
        )

        await create_evaluation_analysis(session, evaluation_analysis)

        # Extract and update AI fields in evaluation
        await update_evaluation_ai_fields(session, evaluation_id, operative_view, len(segments))

        # Rebuild timeline events for this evaluation after each processing run
        await rebuild_timeline_events(session, evaluation_id, segments, operative_view)

        # Persist interaction phases (ENTRY → ATTENTION → CLOSURE, etc.)
        from app.services.interaction_phase_services import persist_interaction_phases
        await persist_interaction_phases(session, evaluation_id, operative_view)

        # Auto-generate action plans based on AI thresholds (IRD, IOC, CES)
        from app.services.action_plan_services import auto_generate_action_plans
        ev = await session.get(__import__("app.models.evaluation_model", fromlist=["Evaluation"]).Evaluation, evaluation_id)
        if ev and ev.campaigns_id:
            from app.models.campaign_model import Campaign
            campaign = await session.get(Campaign, ev.campaigns_id)
            if campaign and campaign.company_id:
                await auto_generate_action_plans(
                    session, evaluation_id, campaign.company_id, operative_view
                )

        return "✅ Transcripción completada y guardada."

    except Exception:
        logger.exception(
            "Audio pipeline failed evaluation_id=%s video_uid=%s",
            evaluation_id,
            video_uid,
        )
        return None

    finally:
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)
                logger.debug("Removed temp file path=%s", f)


async def reprocess_transcription_only(
    video_uid: str,
    evaluation_id: int,
    session: AsyncSession,
) -> str | None:
    """
    Vuelve a procesar desde el vídeo ya en Cloudflare Stream (sin nueva subida):
    descarga, extrae audio, sube MP3 a R2, Whisper + diarización, y opcionalmente
    regenera el MP4 de entrega en R2 (mismo criterio que el pipeline principal).

    Reemplaza segmentos y `transcript_text` del análisis. No ejecuta GPT ni
    actualiza campos IA de la evaluación.
    """
    from app.services.openai_services import transcribe_audio_segments_only
    from app.services.transcript_segment_services import (
        create_transcript_segments,
        delete_segments_for_evaluation,
        update_evaluation_analysis_transcript_text,
    )

    id_archivo = str(uuid.uuid4())
    tmp_dir = tempfile.gettempdir()
    video_path = f"{tmp_dir}/retr_{id_archivo}.mp4"
    audio_path = f"{tmp_dir}/retr_{id_archivo}.mp3"

    try:
        is_ready = await wait_until_ready_to_stream(video_uid)
        if not is_ready:
            logger.warning(
                "reprocess_transcription_only: video not ready evaluation_id=%s",
                evaluation_id,
            )
            return None

        await enable_download(video_uid)
        success, _ = await wait_and_download_video(video_uid, video_path)
        if not success:
            logger.error(
                "reprocess_transcription_only: download failed evaluation_id=%s",
                evaluation_id,
            )
            return None

        await run_in_threadpool(extract_audio, video_path, audio_path)

        r2_audio_key = f"audios/{id_archivo}.mp3"
        logger.info(
            "reprocess_transcription_only: uploading audio to R2 evaluation_id=%s key=%s",
            evaluation_id,
            r2_audio_key,
        )
        await run_in_threadpool(
            r2_upload, archivo_local=audio_path, nombre_objetivo=r2_audio_key
        )

        segments, full_transcript = await run_in_threadpool(
            transcribe_audio_segments_only, audio_path
        )

        if settings.DELIVERY_VIDEO_ENABLED and segments:
            from app.services.video_delivery_edit_services import (
                compose_and_upload_delivery_video,
            )

            dk = await compose_and_upload_delivery_video(
                session, evaluation_id, video_path, segments
            )
            if dk:
                logger.info(
                    "reprocess_transcription_only: delivery video refreshed evaluation_id=%s key=%s",
                    evaluation_id,
                    dk,
                )

        await delete_segments_for_evaluation(session, evaluation_id)
        await create_transcript_segments(
            session, evaluation_id, segments, do_commit=False
        )
        await update_evaluation_analysis_transcript_text(
            session, evaluation_id, full_transcript
        )
        await session.commit()
        logger.info(
            "reprocess_transcription_only OK evaluation_id=%s segments=%s",
            evaluation_id,
            len(segments),
        )
        return f"segments={len(segments)}"
    except Exception:
        logger.exception(
            "reprocess_transcription_only failed evaluation_id=%s", evaluation_id
        )
        await session.rollback()
        return None
    finally:
        for f in (video_path, audio_path):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass


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
            logger.warning(
                "Evaluation not found for AI field update evaluation_id=%s",
                evaluation_id,
            )
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
        logger.info("AI fields updated evaluation_id=%s", evaluation_id)

    except json.JSONDecodeError as e:
        logger.warning(
            "Could not parse operative view as JSON evaluation_id=%s: %s",
            evaluation_id,
            e,
        )
    except Exception as e:
        logger.warning(
            "Error updating AI fields evaluation_id=%s: %s", evaluation_id, e
        )


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

    try:
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
            logger.warning(
                "Could not parse operative JSON for events evaluation_id=%s",
                evaluation_id,
            )
        except Exception as exc:
            logger.warning(
                "Error creating events from operative JSON evaluation_id=%s: %s",
                evaluation_id,
                exc,
            )

        if events:
            await create_events_batch(session, evaluation_id, events)
            logger.info(
                "Timeline events saved evaluation_id=%s count=%s",
                evaluation_id,
                len(events),
            )
    except ProgrammingError as exc:
        if is_undefined_evaluation_events_table_error(exc):
            await session.rollback()
            logger.warning(
                "evaluation_events table missing; skipping timeline rebuild "
                "evaluation_id=%s (run alembic upgrade to create it)",
                evaluation_id,
            )
            return
        raise
