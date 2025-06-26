from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def audio_analysis(audio_path: str):
    # 1. Transcribir el audio
    with open(audio_path, "rb") as audio_file:
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
            language="es",  # O "en", según el idioma del audio
        )

    transcription = transcript_response

    # 2. Analizar la transcripción con GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en análisis de audio. Recibirás un texto transcrito de un audio y deberás:\n"
                "1. Resumir lo que se dijo.\n"
                "2. Identificar los temas principales.\n"
                "3. Evaluar el tono emocional del hablante.\n"
                "4. Indicar si hay múltiples participantes y quiénes parecen ser.",
            },
            {
                "role": "user",
                "content": f"Este es el texto transcrito del audio:\n\n{transcription}",
            },
        ],
    )

    return response.choices[0].message.content
