import logging

from openai import OpenAI
from app.core.config import settings
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def _transcript_confidence_preamble(segments: List[Dict[str, Any]]) -> str:
    """Si los segmentos tienen logprob bajo, avisar al modelo de análisis (GPT)."""
    probs = [
        float(s["avg_logprob"])
        for s in segments
        if s.get("avg_logprob") is not None
    ]
    if not probs:
        return ""
    mean_lp = sum(probs) / len(probs)
    if mean_lp >= -0.78:
        return ""
    return (
        "[Calidad de la transcripción automática] La confianza media del reconocimiento "
        "de voz es baja. Cita solo frases que aparezcan en el texto; si el audio es "
        "ambiguo, dilo explícitamente. El contenido está en español.\n\n"
    )


def _whisper_segment_to_dict(seg: Any) -> Dict[str, Any]:
    """Normalize Whisper segment objects (dict, Pydantic model, or attribute object)."""
    if seg is None:
        return {}
    if isinstance(seg, dict):
        return {
            "start": float(seg.get("start", 0)),
            "end": float(seg.get("end", 0)),
            "text": str(seg.get("text", "")).strip(),
            "avg_logprob": seg.get("avg_logprob"),
        }
    model_dump = getattr(seg, "model_dump", None)
    if callable(model_dump):
        return _whisper_segment_to_dict(model_dump())
    return {
        "start": float(getattr(seg, "start", 0)),
        "end": float(getattr(seg, "end", 0)),
        "text": str(getattr(seg, "text", "")).strip(),
        "avg_logprob": getattr(seg, "avg_logprob", None),
    }


def audio_analysis(audio_path: str) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Transcribe and analyze audio
    
    Returns:
        Tuple of (analysis_text, segments_list, full_transcript_text)
        - analysis_text: The GPT analysis result
        - segments_list: List of {start, end, text} from Whisper
        - full_transcript_text: Complete transcript as string
    """
    # 1. Transcribir el audio
    with open(audio_path, "rb") as audio_file:
        # No usar `prompt` de sesgo léxico largo aquí: en verbose_json Whisper puede
        # repetir ese texto en muchos segmentos en lugar del audio real.
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            language="es",
        )

    segments: List[Dict[str, Any]] = []
    raw_segments = getattr(transcript_response, "segments", None) or []
    for seg in raw_segments:
        d = _whisper_segment_to_dict(seg)
        if d.get("text"):
            segments.append(d)

    # 1b. Speaker diarization (pyannote si HF_TOKEN configurado, heurística si no)
    try:
        from app.services.diarization_services import assign_speakers
        segments = assign_speakers(audio_path, segments)
        logger.info("Speaker diarization applied segment_count=%s", len(segments))
    except Exception as exc:
        logger.warning("Speaker diarization skipped: %s", exc)

    # Get full transcript text (con etiquetas de hablante si están disponibles)
    _has_speakers = any(seg.get("speaker") not in (None, "UNKNOWN") for seg in segments)
    if _has_speakers:
        full_transcript = "\n".join(
            f"[{seg.get('speaker', 'UNKNOWN')}] {seg['text']}" for seg in segments
        )
    else:
        full_transcript = transcript_response.text if hasattr(transcript_response, "text") else str(transcript_response)

    # 2. Analizar la transcripción con GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                    Necesito modificar el prompt pues en el anterior hay algunas subjetividades en adicion este tiene json que permite robustecer el analisis y la presentacion frente al cliente. role: >
                    Eres un analista dual de Customer Experience (CX) con enfoque consultivo y metodológico. 
                    Debes entregar un análisis balanceado entre storytelling ejecutivo y consistencia cuantitativa.  
                    Tu trabajo debe alinearse con las mejores prácticas de la disciplina (Forrester CX Index, 
                    NPS de Bain & Company, Customer Effort Score de Gartner, estándares de CXPA y Harvard Business Review).  

                    idioma: >
                    La transcripción está en español; conserva matices del castellano y no traduzcas verbatims
                    a otro idioma salvo que el cliente lo pida explícitamente.

                    contexto: >
                    Recibirás una transcripción de interacción entre cliente y agente (real o mystery shopper).  
                    Tu misión es producir dos vistas:  
                    1) *Vista Ejecutiva Consultiva* para directivos (narrativa, insights, emociones, acciones).  
                    2) *Vista Operativa Metodológica* en formato JSON rígido (KPIs, verbatims, acciones automáticas).  

                    objetivo: >
                    Generar un análisis profundo, estratégico y a la vez estructurado, 
                    capaz de alimentar dashboards, informes ejecutivos y modelos de entrenamiento.  

                    estructura_de_salida:  

                    # -------------------
                    # 1. Vista Ejecutiva (Consultiva)
                    # -------------------
                    Vista_Ejecutiva:
                        1. 🧾 Resumen ejecutivo (3 líneas máx.)
                        2. 🧠 Mini transcripción clave (máx. 2–3 frases textuales)
                        3. 📌 Temas principales tratados
                        4. 😐 Tono emocional cliente y agente (con evidencia)
                        5. 👥 Identificación de roles
                        6. 📊 Evaluación cuantitativa (escala 1–5):
                        - saludo_bienvenida
                        - escucha_activa
                        - claridad_en_la_información
                        - resolución_del_problema
                        - empatía
                        - cierre_de_conversación
                        - profesionalismo_general
                        7. ✅ Buenas prácticas observadas
                        8. ⚠ Oportunidades de mejora:
                        - operativas
                        - emocionales
                        9. 🚀 Oportunidades de entrenamiento específicas
                        10. 🔥 Frases críticas detectadas
                        11. 💬 Recomendaciones accionables (alta / media / baja prioridad)
                        12. 📈 NPS inferido:
                            - valor (0–10)
                            - clasificación (Detractor, Pasivo, Promotor)
                            - justificación emocional y racional
                        13. 🧩 Impacto estimado en el negocio:
                            - tipo (Emocional / Operativo / Reputacional / Económico)
                            - riesgo_oportunidad (qué se gana o pierde si no se mejora)

                    # -------------------
                    # 2. Vista Operativa (Metodológica JSON)
                    # -------------------
                    Vista_Operativa_JSON: >
                        Debe entregarse en formato JSON estricto. No inventes ni modifiques campos.  
                        Usa null si un dato no está disponible.  
                        Aplica las siguientes reglas deterministas:  

                        1. IOC – Índice de Oportunidad Comercial
                        - 100 = oportunidad identificada y gestionada
                        - 50  = identificada pero mal gestionada
                        - 0   = ignorada o no relevante

                        2. IRD – Índice de Riesgo de Deserción
                        - 100 = hostilidad, sin solución, abandono
                        - 50  = incomodidad moderada
                        - 0   = sin señales de riesgo

                        3. CES – Customer Effort Score (simulado)
                        - 0   = sin esfuerzo
                        - 25  = repregunta leve
                        - 50  = 2 repreguntas o espera >30s
                        - 75  = 3+ repreguntas/insistencias
                        - 100 = abandono por falta de respuesta

                        4. Calidad Básica:
                        - saludo
                        - identificacion
                        - ofrecimiento
                        - cierre
                        - valor_agregado

                        5. Verbatims:
                        - hasta 3 frases exactas con origen (cliente/colaborador) y timestamp (mm:ss)
                        - clasificados en positivos, negativos o críticos

                        6. Acciones sugeridas automáticas:
                        - Si IRD > 70 → "Revisar entrenamiento de cortesía en sucursal"
                        - Si IOC < 40 → "Capacitar en prospección de productos"
                        - Si CES > 60 → "Simplificar procesos de información"
                        
                        7. AI Extracted Fields (REQUIRED - add to JSON):
                        - customer_emotion: string (e.g., "frustrado", "satisfecho", "neutral")
                        - agent_emotion: string (e.g., "profesional", "apático", "amable")
                        - problem_resolved: boolean
                        - product_offered: boolean
                        - nps_inferred: integer 0-10
                        - greeting_detected: boolean

                        Estructura JSON obligatoria:

                        json
                        {
                        "id_entrevista": "string",
                        "timestamp_analisis": "YYYY-MM-DD HH:MM:SS",
                        "metadata": {
                            "canal": "callcenter/whatsapp/presencial",
                            "duracion_segundos": 0,
                            "pais": "string",
                            "sucursal_id": "string",
                            "segmento_cliente": "string"
                        },
                        "IOC": {
                            "score": 0,
                            "justificacion": "Texto breve"
                        },
                        "IRD": {
                            "score": 0,
                            "justificacion": "Texto breve"
                        },
                        "CES": {
                            "score": 0,
                            "justificacion": "Texto breve"
                        },
                        "Calidad": {
                            "saludo": false,
                            "identificacion": false,
                            "ofrecimiento": false,
                            "cierre": false,
                            "valor_agregado": false
                        },
                        "Verbatims": {
                            "positivos": [],
                            "negativos": [],
                            "criticos": []
                        },
                        "acciones_sugeridas": [],
                        "ai_extracted": {
                            "customer_emotion": "string",
                            "agent_emotion": "string", 
                            "problem_resolved": false,
                            "product_offered": false,
                            "nps_inferred": 0,
                            "greeting_detected": false
                        },
                        "interaction_phases": [
                            {
                                "phase": "ENTRY",
                                "label": "Entrada / Bienvenida",
                                "start_seconds": 0,
                                "end_seconds": 30,
                                "summary": "Descripción breve de lo que ocurre en esta fase"
                            },
                            {
                                "phase": "ATTENTION",
                                "label": "Atención / Gestión",
                                "start_seconds": 30,
                                "end_seconds": 120,
                                "summary": "Descripción breve"
                            },
                            {
                                "phase": "CLOSURE",
                                "label": "Cierre / Despedida",
                                "start_seconds": 120,
                                "end_seconds": 180,
                                "summary": "Descripción breve"
                            }
                        ]
                        }

                    IMPORTANTE para interaction_phases:
                    - Detecta los momentos reales de la interacción basándote en el contenido.
                    - Los timestamps deben ser los segundos exactos de inicio/fin de cada fase.
                    - Si hay fases adicionales (espera, escalamiento, etc.) agrégalas.
                    - Usa SIEMPRE los valores de phase: ENTRY, ATTENTION, CLOSURE, WAITING, ESCALATION, OTHER.

                    formato: >
                    Entrega SIEMPRE las dos vistas en orden:  
                    1) Vista Ejecutiva (texto consultivo con íconos y bullets).  
                    2) Vista Operativa (JSON).  
                    Ambas deben derivar de la misma transcripción analizada.
                """,
            },
            {
                "role": "user",
                "content": (
                    f"{_transcript_confidence_preamble(segments)}"
                    f"Este es el texto transcrito del audio (español):\n\n{full_transcript}"
                ),
            },
        ],
        temperature=0,
    )

    analysis_result = response.choices[0].message.content
    
    return analysis_result, segments, full_transcript
