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
                "content": "Eres un analista experto en experiencia del cliente (CX), especializado en interacciones de mystery shopper. Recibirás la transcripción de una conversación y deberás hacer un análisis profundo, estructurado y accionable para uso en dashboards.\n"
                "Incluye:\n"
                "1. Resumen detallado de la conversación.\n"
                "2. Temas principales tratados.\n"
                "3. Tono emocional de cada participante (cliente y agente).\n"
                "4. Identificación de participantes y sus roles.\n"
                "5. Evaluación cuantitativa (1–5) con comentarios en: Saludo y bienvenida, Escucha activa, Claridad en la información, Resolución del problema, Empatía, Cierre de conversación, Profesionalismo general\n6. ✅ Buenas prácticas observadas.\n7. ⚠ Fallas o áreas de mejora.\n8. 🚀 Oportunidades de entrenamiento específicas.\n9. 🔥 Frases críticas detectadas (como “cancelar”, “no vuelvo”, “molesto”).\n10. 💬 Recomendaciones accionables para mejorar la experiencia.\n"
                "11. NPS estimado (según lenguaje del cliente y resultados): Valor entre 0 y 10, Clasificación como Detractor( (0–6), Pasivo (7–8) o Promotor (9–10) ), Justificación textual del puntaje",
            },
            {
                "role": "user",
                "content": f"Este es el texto transcrito del audio:\n\n{transcription}",
            },
        ],
    )

    return response.choices[0].message.content
