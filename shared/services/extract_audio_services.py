# shared/services/extract_audio_services.py

from analysis.services.extract_audio_services import handle_stream_to_audio as _handle_stream_to_audio

async def handle_stream_to_audio(*args, **kwargs):
    # Aquí podrías meter validación, logging, timeouts, etc.
    return await _handle_stream_to_audio(*args, **kwargs)
