import asyncio
import os
import random
import tempfile
import time
import uuid

import httpx
from shared.services.sentiment_analysis_services import analyze_sentiment_text
from moviepy import VideoFileClip
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool
from sqlmodel import select

from shared.core.db import get_db
from shared.models.evaluation_analysis_model import EvaluationAnalysisBase
from shared.services.evaluation_analysis_services import (
    create_evaluation_analysis,
    split_analysis,
)
from shared.services.cloudflare_rs_services import r2_upload
from shared.services.cloudflare_stream_services import (
    enable_download,
    get_download_status,
    wait_until_ready_to_stream,
)
from shared.services.openai_services import audio_analysis


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
        await run_in_threadpool(extract_audio, video_path, audio_path)

        print("📤 Subiendo audio a R2...")
        await run_in_threadpool(
            r2_upload, archivo_local=audio_path, nombre_objetivo=r2_key
        )

        print("🧠 Enviando audio...")
        audio_result = await run_in_threadpool(audio_analysis, audio_path)
        sentiment = analyze_sentiment_text(audio_result if isinstance(audio_result, str) else str(audio_result))
        
        print("📊 Sentimiento del transcript:", sentiment)

        print(f"📝 Transcripción completada:\n{audio_result}...")

        print("💾 Guardando análisis de evaluación...")

        executive_view, operative_view = split_analysis(audio_result)

        evaluation_analysis = EvaluationAnalysisBase(
            evaluation_id=evaluation_id,
            analysis=audio_result,
            executive_view=executive_view,
            operative_view=operative_view,
            sentiment=sentiment  # <-- campo extra si lo soporta tu modelo
        )

        db_analysis = await create_evaluation_analysis(session, evaluation_analysis)
        
        # 🧠 INTELLIGENCE ENGINE: Auto-generate insights and tags
        try:
            from shared.services.intelligence_services import (
                generate_insights_from_analysis,
                auto_tag_evaluation,
                check_alert_thresholds
            )
            from shared.models.evaluation_model import Evaluation
            from shared.models.campaign_model import Campaign
            
            # Get evaluation to retrieve company_id
            eval_query = (
                select(Evaluation)
                .where(Evaluation.id == evaluation_id)
            )
            eval_result = await session.execute(eval_query)
            evaluation = eval_result.scalars().first()
            
            if evaluation:
                # Get company_id from campaign
                campaign_query = select(Campaign).where(Campaign.id == evaluation.campaigns_id)
                campaign_result = await session.execute(campaign_query)
                campaign = campaign_result.scalars().first()
                
                if campaign:
                    company_id = campaign.company_id
                    
                    print("🔍 Generando insights automáticos...")
                    insights = await generate_insights_from_analysis(
                        session, evaluation_id, db_analysis, company_id
                    )
                    print(f"✅ {len(insights)} insights generados")
                    
                    print("🏷️ Auto-etiquetando evaluación...")
                    tags = await auto_tag_evaluation(
                        session, evaluation_id, db_analysis
                    )
                    print(f"✅ {len(tags)} etiquetas aplicadas")
                    
                    print("🚨 Verificando alertas...")
                    alerts = await check_alert_thresholds(
                        session, evaluation_id, db_analysis, company_id
                    )
                    print(f"✅ {len(alerts)} alertas generadas")
                    
                    # 📧 NOTIFY CRITICAL INSIGHTS (Email + SMS)
                    critical_insights = [i for i in insights if i.severity in ['critical', 'high']]
                    if critical_insights or alerts:
                        try:
                            from shared.services.notification_integration_services import notification_orchestrator
                            from shared.services.webhook_services import integration_orchestrator
                            from shared.models.user_model import User
                            
                            # Get admin users from company to notify
                            admin_query = select(User).where(
                                User.company_id == company_id,
                                User.role.in_([1, 2]),  # Admin and Manager
                                User.deleted_at == None
                            )
                            admin_result = await session.execute(admin_query)
                            admins = admin_result.scalars().all()
                            
                            for insight in critical_insights:
                                # 📧 Email/SMS notifications to admins
                                for admin in admins:
                                    print(f"📧 Notificando insight crítico a {admin.email}...")
                                    await notification_orchestrator.notify_critical_insight(
                                        session=session,
                                        user=admin,
                                        insight_type=insight.insight_type,
                                        severity=insight.severity,
                                        title=insight.title,
                                        description=insight.description,
                                        evaluation_id=evaluation_id
                                    )
                                
                                # 🔔 Slack + Webhooks
                                print(f"🔔 Enviando webhooks para insight: {insight.title}")
                                await integration_orchestrator.notify_critical_insight(
                                    session=session,
                                    company_id=company_id,
                                    insight_type=insight.insight_type,
                                    severity=insight.severity,
                                    title=insight.title,
                                    description=insight.description,
                                    evaluation_id=evaluation_id,
                                    suggested_actions=insight.suggested_actions
                                )
                            
                            print(f"📧 {len(critical_insights)} notificaciones enviadas (email + webhooks)")
                        except Exception as notify_error:
                            print(f"⚠️ Error en notificaciones (no crítico): {notify_error}")
                            
        except Exception as intel_error:
            print(f"⚠️ Error en intelligence engine (no crítico): {intel_error}")
            # Continue even if intelligence fails

        return "✅ Transcripción completada y guardada."

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        return None

    finally:
        for f in [video_path, audio_path]:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Archivo temporal eliminado: {f}")
