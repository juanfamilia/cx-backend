from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def audio_analysis(audio_path: str):
    with open(audio_path, "rb") as audio_file:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en análisis de audio. Recibirás un audio y deberás:\n"
                    "1. Resumir lo que se dijo.\n"
                    "2. Identificar los temas principales.\n"
                    "3. Evaluar el tono emocional del hablante.\n"
                    "4. Indicar si hay múltiples participantes y quiénes parecen ser.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza el siguiente audio:"},
                        {
                            "type": "audio",
                            "audio": {
                                "file": audio_file,
                                "media_type": "audio/mpeg",
                            },
                        },
                    ],
                },
            ],
        )

    return response.choices[0].message.content
