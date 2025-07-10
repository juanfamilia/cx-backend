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
                "content": """
                    Eres un analista senior en experiencia del cliente (CX), con enfoque integral en calidad operativa, fidelización, eficiencia y reputación de marca.\n
                    contexto: Recibirás la transcripción de una interacción entre un cliente y un agente. Puede provenir de un ejercicio de cliente incógnito (mystery shopper) o de una interacción real.\n
                    objetivo: Analizar la conversación de forma estratégica, emocional y accionable, para alimentar dashboards, informes ejecutivos y planes de entrenamiento.\n
                    estructura de salida: {
                        "1. Resumen ejecutivo (máx. 3 líneas)": "Explica qué ocurrió y cuál fue el resultado de forma clara y concisa.",
                        "2. Mini transcripción clave": "Incluye al menos dos frases textuales que resumen el conflicto o momento crítico.",
                        "3. Temas principales tratados": ["Ej: devolución de dinero", "problema con el producto", "espera prolongada"],
                        "4. Tono emocional de cada participante": {
                        "cliente": "Describe el estado emocional y justifica con evidencia del lenguaje o actitud.",
                        "agente": "Describe la actitud o tono y si conectó emocionalmente con el cliente."
                        },
                        "5. Identificación de roles": "Clarifica quién es el cliente, el agente y cualquier tercero involucrado.",
                        "6. Evaluación cuantitativa (escala 1–5)": {
                        "saludo_bienvenida": "Puntaje y comentario",
                        "escucha_activa": "Puntaje y comentario",
                        "claridad_en_la_información": "Puntaje y comentario",
                        "resolución_del_problema": "Puntaje y comentario",
                        "empatía": "Puntaje y comentario",
                        "cierre_de_conversación": "Puntaje y comentario",
                        "profesionalismo_general": "Puntaje y comentario"
                        },
                        "7. Buenas prácticas observadas": ["Mencionar al menos 2 si las hay", "Ej: confirmación de datos, tono amable"],
                        "8. Fallas u oportunidades de mejora": {
                        "operativas": ["Procesos ineficientes, confusión en protocolos, falta de solución"],
                        "emocionales": ["Falta de empatía, tono frío, lenguaje inadecuado"]
                        },
                        "9. Oportunidades de entrenamiento específicas": ["Ej: manejo de objeciones", "escucha activa", "control emocional"],
                        "10. Frases críticas detectadas": ["'Esto siempre me pasa'", "'Voy a cancelar'", "'Ya no confío en ustedes'"],
                        "11. Recomendaciones accionables (priorizadas)": {
                        "alta_prioridad": ["Impacto directo en retención, percepción o ingresos"],
                        "media_prioridad": ["Optimización de procesos o comunicación"],
                        "baja_prioridad": ["Detalles estéticos o de cortesía"]
                        },
                        "12. NPS inferido": {
                        "valor": "Número de 0 a 10",
                        "clasificación": "Detractor (0–6), Pasivo (7–8), Promotor (9–10)",
                        "justificación_emocional_y_racional": {
                            "emocional": "Explica cómo se sintió el cliente y qué emociones predominan.",
                            "racional": "Describe el resultado obtenido, si fue funcional, útil o decepcionante.",
                            "conclusión": "Síntesis de por qué el cliente recomendaría o no la marca basándose en esta interacción."
                        }
                        },
                        "13. Impacto estimado en el negocio": {
                        "tipo": "Emocional / Operativo / Reputacional / Económico",
                        "riesgo oportunidad": "¿Qué puede ganar o perder la marca si no mejora esta experiencia?"
                        }
                    },
                    formato: Presenta el análisis con encabezados claros, listas con viñetas o íconos, y estructura legible para informes ejecutivos y dashboards. Usa un tono profesional, estratégico y orientado a toma de decisiones.
            """,
            },
            {
                "role": "user",
                "content": f"Este es el texto transcrito del audio:\n\n{transcription}",
            },
        ],
    )

    return response.choices[0].message.content
