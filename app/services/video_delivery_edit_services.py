"""
Vídeo de “entrega”: pantalla inicial (sucursal + áreas evaluadas) y supresión de audio
en tramos donde se detecten datos sensibles (p. ej. número de cuenta).

- Intro: imagen generada con Pillow + mux con ffmpeg (misma resolución que el vídeo).
- Silencios: pydub sobre la pista de audio + remux con ffmpeg.
- Detección: reglas por texto en segmentos de Whisper; opcionalmente Claude (Anthropic)
  para mejorar recall/precisión si ANTHROPIC_API_KEY está definida.

No sustituye revisión legal: combinar heurística + revisión humana para casos límite.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import subprocess
import tempfile
import uuid
from typing import Any, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.branch_model import Branch
from app.models.campaign_model import Campaign
from app.models.evaluation_model import Evaluation
from app.models.zone_model import Zone

logger = logging.getLogger(__name__)

_INTRO_SECONDS = 5.0
_PADDING_SEC = 0.35
# Tarjetas / cuentas: 10+ dígitos seguidos o típicos grupos de 4
_RE_ACCOUNTISH = re.compile(
    r"(?:\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}|\d{10,})"
)
_RE_TRIGGERS = re.compile(
    r"(cuenta|clabe|iban|n[uú]mero de cuenta|tarjeta|cvv|nip|pin de)"
    r".{0,40}?\d|\d.{0,40}?(cuenta|clabe|tarjeta)",
    re.IGNORECASE,
)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def ffprobe_video_size(path: str) -> Tuple[int, int]:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            path,
        ],
        text=True,
    )
    data = json.loads(out)
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            return int(s["width"]), int(s["height"])
    raise RuntimeError("No video stream found")


def _regex_sensitive_intervals(segments: List[dict[str, Any]]) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if _RE_ACCOUNTISH.search(text) or _RE_TRIGGERS.search(text):
            start = max(0.0, float(seg.get("start", 0)) - _PADDING_SEC)
            end = float(seg.get("end", 0)) + _PADDING_SEC
            if end > start:
                out.append((start, end))
    return _merge_intervals(out)


def _merge_intervals(intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not intervals:
        return []
    s = sorted(intervals, key=lambda x: x[0])
    merged = [s[0]]
    for a, b in s[1:]:
        la, lb = merged[-1]
        if a <= lb + 0.05:
            merged[-1] = (la, max(lb, b))
        else:
            merged.append((a, b))
    return merged


async def _claude_sensitive_intervals(
    segments: List[dict[str, Any]],
) -> List[Tuple[float, float]]:
    if not settings.ANTHROPIC_API_KEY:
        return []
    # Compactar segmentos para el contexto
    payload = [
        {"start": round(float(s.get("start", 0)), 2), "end": round(float(s.get("end", 0)), 2), "text": (s.get("text") or "")[:500]}
        for s in segments[:200]
    ]
    user_prompt = (
        "Eres un asistente de privacidad para grabaciones de atención al cliente en español.\n"
        "Recibes segmentos con tiempos (segundos) y texto transcrito.\n"
        "Devuelve SOLO un JSON array (sin markdown) de objetos "
        '{"start": number, "end": number} '
        "indicando tramos donde conviene SILENCIAR el audio porque se mencionan "
        "números de cuenta bancaria, tarjeta, CLABE, IBAN, CVV, PIN o lectura de datos "
        "financieros sensibles. Si no hay ninguno, devuelve [].\n"
        "No incluyas teléfonos genéricos de 10 dígitos salvo que vayan con palabras como cuenta/tarjeta.\n"
        f"Segmentos:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            r.raise_for_status()
            body = r.json()
            text = ""
            for block in body.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            arr = json.loads(text)
            out: List[Tuple[float, float]] = []
            for item in arr:
                if isinstance(item, dict) and "start" in item and "end" in item:
                    a, b = float(item["start"]), float(item["end"])
                    if b > a:
                        out.append((max(0.0, a - _PADDING_SEC), b + _PADDING_SEC))
            return _merge_intervals(out)
    except Exception as exc:
        logger.warning("Claude PII interval refinement failed: %s", exc)
        return []


async def collect_delivery_metadata(
    session: AsyncSession, evaluation_id: int
) -> dict[str, Any]:
    ev = await session.get(Evaluation, evaluation_id)
    if not ev:
        raise ValueError("Evaluation not found")

    branch_label = ev.branch_name or (ev.branch_id or "")
    if ev.branch_fk_id:
        br = await session.get(Branch, ev.branch_fk_id)
        if br:
            branch_label = br.name or branch_label

    zone_names: list[str] = []
    if ev.visited_zones:
        zq = select(Zone).where(Zone.id.in_(tuple(ev.visited_zones)))
        rows = (await session.execute(zq)).scalars().all()
        by_id = {z.id: z.name for z in rows}
        for zid in ev.visited_zones:
            if zid in by_id:
                zone_names.append(by_id[zid])

    company_name = ""
    if ev.campaigns_id:
        camp = await session.get(Campaign, ev.campaigns_id)
        if camp and camp.company_id:
            from app.models.company_model import Company

            co = await session.get(Company, camp.company_id)
            if co:
                company_name = co.name or ""

    return {
        "evaluation_id": evaluation_id,
        "company_name": company_name,
        "branch_label": branch_label or "Sucursal no indicada",
        "areas": zone_names,
        "interaction_type": getattr(ev.interaction_type, "value", str(ev.interaction_type or "")),
        "interaction_date": str(ev.interaction_date or ""),
    }


def _draw_intro_image(meta: dict[str, Any], width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), color=(18, 24, 38))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 42)
        body_font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    y = int(height * 0.08)
    title = "Evaluación — vídeo de entrega"
    draw.text((int(width * 0.06), y), title, fill=(240, 244, 255), font=title_font)
    y += 70
    lines = [
        f"Empresa: {meta.get('company_name') or '—'}",
        f"Sucursal: {meta.get('branch_label') or '—'}",
    ]
    areas = meta.get("areas") or []
    if areas:
        lines.append("Áreas evaluadas:")
        lines.extend(f"  • {a}" for a in areas[:12])
        if len(areas) > 12:
            lines.append(f"  … (+{len(areas) - 12} más)")
    else:
        lines.append("Áreas evaluadas: — (no registradas en la evaluación)")
    if meta.get("interaction_date"):
        lines.append(f"Fecha de interacción: {meta['interaction_date']}")
    for line in lines:
        draw.text((int(width * 0.06), y), line, fill=(210, 218, 235), font=body_font)
        y += 36
        if y > height - 80:
            break
    draw.text(
        (int(width * 0.06), height - 55),
        "Los tramos con posibles datos financieros sensibles se silencian automáticamente.",
        fill=(140, 150, 170),
        font=body_font,
    )
    return img


def _build_intro_mp4(meta: dict[str, Any], main_video_path: str, intro_mp4_path: str) -> None:
    w, h = ffprobe_video_size(main_video_path)
    img = _draw_intro_image(meta, w, h)
    png_buf = io.BytesIO()
    img.save(png_buf, format="PNG")
    png_buf.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        tf.write(png_buf.read())
        png_path = tf.name
    try:
        _run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                png_path,
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t",
                str(_INTRO_SECONDS),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                intro_mp4_path,
            ]
        )
    finally:
        if os.path.exists(png_path):
            os.unlink(png_path)


def _mute_audio_segments(
    video_path: str, intervals: List[Tuple[float, float]], out_video_path: str
) -> None:
    audio = AudioSegment.from_file(video_path)
    duration_ms = len(audio)
    ranges_ms: List[Tuple[int, int]] = []
    for a, b in intervals:
        s = max(0, int(a * 1000))
        e = min(duration_ms, int(b * 1000))
        if e > s:
            ranges_ms.append((s, e))
    ranges_ms.sort(reverse=True)
    out_audio = audio
    for s, e in ranges_ms:
        silence = AudioSegment.silent(duration=e - s)
        out_audio = out_audio[:s] + silence + out_audio[e:]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wf:
        wav_path = wf.name
    try:
        out_audio.export(wav_path, format="wav")
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                wav_path,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                out_video_path,
            ]
        )
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)


def _concat_videos(intro_path: str, body_path: str, out_path: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as lf:
        # Rutas absolutas para concat demuxer
        lf.write(f"file '{os.path.abspath(intro_path)}'\n")
        lf.write(f"file '{os.path.abspath(body_path)}'\n")
        list_path = lf.name
    try:
        _run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path,
                "-c",
                "copy",
                out_path,
            ]
        )
    finally:
        os.unlink(list_path)


async def compose_and_upload_delivery_video(
    session: AsyncSession,
    evaluation_id: int,
    source_video_path: str,
    segments: List[dict[str, Any]],
) -> Optional[str]:
    """
    Genera MP4 de entrega en R2. Devuelve la object key o None si está deshabilitado / falla.
    """
    if not settings.DELIVERY_VIDEO_ENABLED:
        logger.info("Delivery video skipped (DELIVERY_VIDEO_ENABLED=false)")
        return None

    meta = await collect_delivery_metadata(session, evaluation_id)
    tmp = tempfile.gettempdir()
    uid = uuid.uuid4().hex
    intro_mp4 = os.path.join(tmp, f"intro_{uid}.mp4")
    body_mp4 = os.path.join(tmp, f"body_{uid}.mp4")
    final_mp4 = os.path.join(tmp, f"delivery_{uid}.mp4")

    try:
        _build_intro_mp4(meta, source_video_path, intro_mp4)

        regex_iv = _regex_sensitive_intervals(segments)
        claude_iv = await _claude_sensitive_intervals(segments)
        merged = _merge_intervals(regex_iv + claude_iv)
        logger.info(
            "Delivery video sensitive intervals evaluation_id=%s count=%s",
            evaluation_id,
            len(merged),
        )

        if merged:
            _mute_audio_segments(source_video_path, merged, body_mp4)
        else:
            body_mp4 = source_video_path

        _concat_videos(intro_mp4, body_mp4, final_mp4)

        r2_key = f"delivery/evaluation-{evaluation_id}.mp4"
        from app.services.cloudflare_rs_services import r2_upload

        r2_upload(archivo_local=final_mp4, nombre_objetivo=r2_key)
        logger.info("Delivery video uploaded key=%s", r2_key)
        return r2_key
    except Exception:
        logger.exception("compose_and_upload_delivery_video failed evaluation_id=%s", evaluation_id)
        return None
    finally:
        for p in (intro_mp4, final_mp4):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        if body_mp4 != source_video_path and os.path.exists(body_mp4):
            try:
                os.unlink(body_mp4)
            except OSError:
                pass
