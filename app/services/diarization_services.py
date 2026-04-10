"""
Speaker diarization service.

Estrategia:
1. Si HF_TOKEN está configurado, usa pyannote.audio (diarización real).
2. Fallback: heurística basada en pausas entre segmentos de Whisper.

El resultado es una lista de segmentos con campo 'speaker' asignado:
  "AGENT"   → empleado (voz predominante al inicio)
  "CLIENT"  → cliente
  "UNKNOWN" → no determinado
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

SpeakerLabel = str  # "AGENT" | "CLIENT" | "UNKNOWN"

# Cuántos segundos de pausa entre segmentos se consideran cambio de turno
_PAUSE_THRESHOLD_SECONDS = 1.2


def _assign_speakers_heuristic(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Heurística simple cuando pyannote no está disponible:
    - Alterna hablante cada vez que hay una pausa >= _PAUSE_THRESHOLD_SECONDS.
    - El primer hablante se asigna como AGENT (el colaborador empieza la interacción).
    """
    if not segments:
        return segments

    labeled = []
    current_speaker: SpeakerLabel = "AGENT"
    prev_end: float = segments[0]["start"]

    for seg in segments:
        pause = seg["start"] - prev_end
        if pause >= _PAUSE_THRESHOLD_SECONDS:
            current_speaker = "CLIENT" if current_speaker == "AGENT" else "AGENT"
        labeled.append({**seg, "speaker": current_speaker})
        prev_end = seg["end"]

    return labeled


def _assign_speakers_pyannote(
    audio_path: str, segments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Diarización real con pyannote.audio.
    Asigna a cada segmento de Whisper el hablante con mayor solapamiento temporal.
    AGENT = speaker con mayor tiempo total hablando (el colaborador suele hablar más).
    """
    try:
        from pyannote.audio import Pipeline  # type: ignore
        import torch  # type: ignore

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=settings.HF_TOKEN,
        )
        if torch.cuda.is_available():
            pipeline = pipeline.to(torch.device("cuda"))

        diarization = pipeline(audio_path)

        # Construir mapa de intervalos → speaker desde pyannote
        speaker_intervals: List[Dict] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_intervals.append(
                {"start": turn.start, "end": turn.end, "speaker": speaker}
            )

        # Determinar quién habla más tiempo → ese es el AGENT
        speaker_time: Dict[str, float] = {}
        for iv in speaker_intervals:
            spk = iv["speaker"]
            speaker_time[spk] = speaker_time.get(spk, 0) + (iv["end"] - iv["start"])

        agent_raw = max(speaker_time, key=lambda s: speaker_time[s]) if speaker_time else None

        def _best_speaker_for_segment(start: float, end: float) -> SpeakerLabel:
            best: Optional[str] = None
            best_overlap = 0.0
            for iv in speaker_intervals:
                overlap = min(end, iv["end"]) - max(start, iv["start"])
                if overlap > best_overlap:
                    best_overlap = overlap
                    best = iv["speaker"]
            if best is None:
                return "UNKNOWN"
            return "AGENT" if best == agent_raw else "CLIENT"

        return [
            {**seg, "speaker": _best_speaker_for_segment(seg["start"], seg["end"])}
            for seg in segments
        ]

    except Exception as exc:
        logger.warning(
            "pyannote diarization failed (%s), falling back to heuristic", exc
        )
        return _assign_speakers_heuristic(segments)


def assign_speakers(
    audio_path: str, segments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Punto de entrada principal.
    Usa pyannote si HF_TOKEN está disponible, heurística en caso contrario.
    """
    if getattr(settings, "HF_TOKEN", None):
        logger.info("Running pyannote speaker diarization path=%s", audio_path)
        return _assign_speakers_pyannote(audio_path, segments)

    logger.info("Running heuristic speaker assignment path=%s", audio_path)
    return _assign_speakers_heuristic(segments)
