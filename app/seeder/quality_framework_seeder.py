"""
Seeder idempotente del Service Quality Framework.

Pobla las tablas globales mantenidas por el superadmin:
  - industries (10 industrias LATAM)
  - quality_frameworks (8 marcos citables)
  - quality_framework_dimensions (dimensiones de cada marco)
  - quality_competencies (~25 competencias operativas)
  - competency_indicators (señales positivas y negativas por competencia)
  - competency_framework_refs (enlace competencia ↔ dimensión de marco)
  - industry_templates (qué competencias aplican a cada industria, con peso)

El seeder es idempotente: usa `code` como clave natural para detectar
si un registro ya existe antes de insertarlo. Se puede ejecutar
múltiples veces sin duplicar datos. Si un registro ya existe, sus
campos NO se sobrescriben (se preserva cualquier edición manual).

Uso:
    python -m app.seeder.quality_framework_seeder

Referencia bibliográfica completa: docs/METHODOLOGY.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.framework_model import Framework, FrameworkDimension
from app.models.industry_model import Industry
from app.models.industry_template_model import IndustryTemplate
from app.models.quality_competency_model import (
    CompetencyCategoryEnum,
    CompetencyFrameworkRef,
    CompetencyIndicator,
    CompetencyMeasurementType,
    IndicatorTypeEnum,
    QualityCompetency,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Datos semilla
# =============================================================================

INDUSTRIES: List[Dict] = [
    {
        "code": "BANCA",
        "name": "Banca y Servicios Financieros",
        "description": (
            "Bancos, cooperativas, financieras, tarjetas de crédito y medios de pago. "
            "Énfasis en confiabilidad, seguridad y cumplimiento normativo."
        ),
        "icon": "bank",
    },
    {
        "code": "RETAIL",
        "name": "Retail y Consumo Masivo",
        "description": (
            "Tiendas físicas y e-commerce, cadenas de consumo. Énfasis en "
            "experiencia de compra, disponibilidad y tangibles."
        ),
        "icon": "shopping-bag",
    },
    {
        "code": "SALUD",
        "name": "Salud y Servicios Médicos",
        "description": (
            "Clínicas, hospitales, seguros médicos, farmacias. Énfasis en "
            "empatía, privacidad de datos y manejo de quejas."
        ),
        "icon": "heart",
    },
    {
        "code": "TELCO",
        "name": "Telecomunicaciones",
        "description": (
            "Operadores de telefonía, internet y TV. Énfasis en bajo esfuerzo "
            "del cliente y resolución en el primer contacto."
        ),
        "icon": "wifi",
    },
    {
        "code": "HORECA",
        "name": "Hotelería, Restaurantes y Cafeterías",
        "description": (
            "Hoteles, restaurantes, bares y cafeterías. Énfasis en momentos "
            "de verdad y atributos atractivos (delighters)."
        ),
        "icon": "coffee",
    },
    {
        "code": "SEGUROS",
        "name": "Seguros",
        "description": (
            "Compañías de seguros y corredores. Énfasis en manejo de "
            "reclamaciones y recuperación de servicio."
        ),
        "icon": "shield",
    },
    {
        "code": "EDUCACION",
        "name": "Educación",
        "description": (
            "Instituciones educativas y plataformas de aprendizaje. Énfasis "
            "en claridad, acompañamiento y atributos atractivos."
        ),
        "icon": "book-open",
    },
    {
        "code": "GOBIERNO",
        "name": "Gobierno y Servicios Ciudadanos",
        "description": (
            "Instituciones públicas, servicios ciudadanos y trámites. "
            "Énfasis en esfuerzo del ciudadano y manejo de quejas."
        ),
        "icon": "landmark",
    },
    {
        "code": "LOGISTICA",
        "name": "Logística y Última Milla",
        "description": (
            "Empresas de courier, transporte y paquetería. Énfasis en "
            "esfuerzo del cliente y recuperación de incidentes."
        ),
        "icon": "truck",
    },
    {
        "code": "TURISMO",
        "name": "Turismo y Experiencias",
        "description": (
            "Agencias de viajes, tours, experiencias turísticas. Énfasis "
            "en momentos de verdad y atributos emocionales."
        ),
        "icon": "map",
    },
]


# Cada framework con su lista de dimensiones
FRAMEWORKS: List[Dict] = [
    {
        "code": "SERVQUAL",
        "name": "SERVQUAL",
        "authors": "Parasuraman, A., Zeithaml, V. A., & Berry, L. L.",
        "year": 1988,
        "source_citation": (
            "Parasuraman, A., Zeithaml, V. A., & Berry, L. L. (1988). "
            "SERVQUAL: A multiple-item scale for measuring consumer "
            "perceptions of service quality. Journal of Retailing, 64(1), 12–40."
        ),
        "url_reference": "https://www.researchgate.net/publication/225083802",
        "description": (
            "Modelo de cinco dimensiones para medir la calidad percibida "
            "del servicio: Tangibles, Confiabilidad, Capacidad de Respuesta, "
            "Seguridad y Empatía."
        ),
        "dimensions": [
            ("SERVQUAL.TANGIBLES", "Tangibles", "Apariencia de instalaciones, equipos, personal y materiales.", 1),
            ("SERVQUAL.RELIABILITY", "Confiabilidad", "Capacidad de realizar el servicio prometido de forma precisa y consistente.", 2),
            ("SERVQUAL.RESPONSIVENESS", "Capacidad de Respuesta", "Disposición para ayudar al cliente y proveer servicio oportuno.", 3),
            ("SERVQUAL.ASSURANCE", "Seguridad", "Conocimiento, cortesía y capacidad de inspirar confianza.", 4),
            ("SERVQUAL.EMPATHY", "Empatía", "Atención individualizada y cuidado al cliente.", 5),
        ],
    },
    {
        "code": "NPS",
        "name": "Net Promoter Score",
        "authors": "Reichheld, F. F.",
        "year": 2003,
        "source_citation": (
            "Reichheld, F. F. (2003). The one number you need to grow. "
            "Harvard Business Review, 81(12), 46–55."
        ),
        "url_reference": "https://hbr.org/2003/12/the-one-number-you-need-to-grow",
        "description": (
            "Indicador de lealtad del cliente en escala 0–10 que clasifica "
            "en Detractores, Pasivos y Promotores."
        ),
        "dimensions": [
            ("NPS.LOYALTY", "Lealtad", "Intención de recomendación del cliente.", 1),
        ],
    },
    {
        "code": "CES",
        "name": "Customer Effort Score",
        "authors": "Dixon, M., Freeman, K., & Toman, N.",
        "year": 2010,
        "source_citation": (
            "Dixon, M., Freeman, K., & Toman, N. (2010). Stop trying to "
            "delight your customers. Harvard Business Review, 88(7/8), 116–122."
        ),
        "url_reference": "https://hbr.org/2010/07/stop-trying-to-delight-your-customers",
        "description": (
            "Métrica de esfuerzo del cliente. Un menor esfuerzo correlaciona "
            "con mayor lealtad más que 'superar expectativas'."
        ),
        "dimensions": [
            ("CES.EFFORT", "Esfuerzo", "Nivel de esfuerzo que debe hacer el cliente para resolver su necesidad.", 1),
        ],
    },
    {
        "code": "FORRESTER_CX",
        "name": "Forrester CX Index",
        "authors": "Forrester Research, Inc.",
        "year": 2016,
        "source_citation": (
            "Forrester Research. (2016). The Forrester Customer Experience "
            "Index methodology. Forrester Research, Inc."
        ),
        "url_reference": "https://www.forrester.com/",
        "description": (
            "Tres pilares para evaluar experiencia del cliente: Efectividad, "
            "Facilidad y Emoción."
        ),
        "dimensions": [
            ("FORRESTER.EFFECTIVENESS", "Efectividad", "El servicio entrega valor real al cliente.", 1),
            ("FORRESTER.EASE", "Facilidad", "El cliente obtiene el valor con el menor esfuerzo.", 2),
            ("FORRESTER.EMOTION", "Emoción", "El cliente se siente bien durante y después de la interacción.", 3),
        ],
    },
    {
        "code": "ISO_18295",
        "name": "ISO 18295 — Centros de Contacto con Clientes",
        "authors": "International Organization for Standardization",
        "year": 2017,
        "source_citation": (
            "International Organization for Standardization. (2017). "
            "ISO 18295-1:2017 Customer contact centres — Part 1: Requirements "
            "for customer contact centres. ISO, Geneva."
        ),
        "url_reference": "https://www.iso.org/standard/64739.html",
        "description": (
            "Requisitos estructurados para la operación de centros de "
            "contacto con clientes, incluyendo competencias del personal "
            "y protocolos de atención."
        ),
        "dimensions": [
            ("ISO18295.CONTACT_REQUIREMENTS", "Requisitos de Contacto", "Requisitos operativos del centro de contacto.", 1),
        ],
    },
    {
        "code": "ISO_10002",
        "name": "ISO 10002 — Manejo de Quejas",
        "authors": "International Organization for Standardization",
        "year": 2018,
        "source_citation": (
            "International Organization for Standardization. (2018). "
            "ISO 10002:2018 Quality management — Customer satisfaction — "
            "Guidelines for complaints handling in organizations. ISO, Geneva."
        ),
        "url_reference": "https://www.iso.org/standard/71580.html",
        "description": (
            "Principios para el tratamiento de quejas: visibilidad, "
            "accesibilidad, capacidad de respuesta, objetividad, "
            "confidencialidad, enfoque al cliente, responsabilidad y mejora."
        ),
        "dimensions": [
            ("ISO10002.COMPLAINT_HANDLING", "Manejo de Quejas", "Tratamiento de quejas y reclamos del cliente.", 1),
        ],
    },
    {
        "code": "COPC_CX",
        "name": "COPC Customer Experience Standard",
        "authors": "COPC Inc.",
        "year": 2022,
        "source_citation": (
            "COPC Inc. (2022). COPC Customer Experience (CX) Standard, "
            "release 6.2. COPC Inc."
        ),
        "url_reference": "https://www.copc.com/",
        "description": (
            "Estándar operativo global para centros de contacto y "
            "experiencia de cliente, con KPIs de eficiencia, calidad y "
            "satisfacción."
        ),
        "dimensions": [
            ("COPC.FCR", "First Contact Resolution", "Resolución en el primer contacto.", 1),
            ("COPC.AHT", "Average Handle Time", "Tiempo promedio de gestión.", 2),
            ("COPC.QUALITY", "Calidad Transaccional", "Calidad evaluada por monitoreo de transacciones.", 3),
        ],
    },
    {
        "code": "KANO",
        "name": "Modelo Kano",
        "authors": "Kano, N., Seraku, N., Takahashi, F., & Tsuji, S.",
        "year": 1984,
        "source_citation": (
            "Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984). "
            "Attractive quality and must-be quality. Journal of the Japanese "
            "Society for Quality Control, 14(2), 39–48."
        ),
        "url_reference": "https://foundationsofhci.com/wp-content/uploads/2020/09/Kano-model.pdf",
        "description": (
            "Clasificación de atributos del servicio en Básicos (Must-be), "
            "De Desempeño (One-dimensional) y Atractivos (Delighters)."
        ),
        "dimensions": [
            ("KANO.MUST_BE", "Básicos (Must-be)", "Atributos cuya ausencia causa insatisfacción; se dan por sentados.", 1),
            ("KANO.ONE_DIMENSIONAL", "De Desempeño", "Atributos donde más es mejor, relación lineal con satisfacción.", 2),
            ("KANO.ATTRACTIVE", "Atractivos (Delighters)", "Atributos que sorprenden positivamente.", 3),
        ],
    },
]


# Competencias. cada una con:
#   - code, name, category, definition, measurement_type, default_weight
#   - ai_field_hint (para mapeo con Evaluation) — puede ser None
#   - framework_refs: list[str] — dimension codes de frameworks
#   - indicators: list[(type, description, detection_hint)]
COMPETENCIES: List[Dict] = [
    # ---------- OPENING ----------
    {
        "code": "GREETING_STANDARD",
        "name": "Saludo y Bienvenida",
        "category": CompetencyCategoryEnum.OPENING,
        "definition": (
            "El colaborador inicia la interacción con un saludo protocolar "
            "apropiado al canal y momento del día."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": "greeting_detected",
        "framework_refs": ["SERVQUAL.RESPONSIVENESS", "ISO18295.CONTACT_REQUIREMENTS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Usa saludo verbal claro (buenos días / tardes / noches).", "buenos días|buenas tardes|buenas noches|hola"),
            (IndicatorTypeEnum.POSITIVE, "Saludo cordial con tono amable.", None),
            (IndicatorTypeEnum.NEGATIVE, "Omite el saludo e inicia directamente con la gestión.", None),
            (IndicatorTypeEnum.NEGATIVE, "Saludo seco o apresurado.", None),
        ],
    },
    {
        "code": "AGENT_IDENTIFICATION",
        "name": "Identificación del Colaborador",
        "category": CompetencyCategoryEnum.OPENING,
        "definition": (
            "El colaborador se identifica por su nombre al inicio de la "
            "interacción."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.ASSURANCE", "ISO18295.CONTACT_REQUIREMENTS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Menciona su nombre propio.", "mi nombre es|soy|le habla|le atiende"),
            (IndicatorTypeEnum.NEGATIVE, "No se identifica durante toda la interacción.", None),
        ],
    },
    {
        "code": "COMPANY_BRANDING",
        "name": "Mención de la Empresa o Marca",
        "category": CompetencyCategoryEnum.OPENING,
        "definition": (
            "El colaborador menciona el nombre de la empresa o marca como "
            "parte del protocolo de apertura."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 0.8,
        "ai_field_hint": None,
        "framework_refs": ["ISO18295.CONTACT_REQUIREMENTS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Menciona la empresa/marca en el saludo inicial.", None),
            (IndicatorTypeEnum.NEGATIVE, "Nunca menciona la empresa durante la interacción.", None),
        ],
    },

    # ---------- ATTENTION ----------
    {
        "code": "ACTIVE_LISTENING",
        "name": "Escucha Activa",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador demuestra escucha activa: deja hablar al cliente, "
            "parafrasea para confirmar entendimiento y no interrumpe."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.5,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.EMPATHY"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Parafrasea lo que dijo el cliente para confirmar entendimiento.", "si entiendo bien|o sea que|me está diciendo que"),
            (IndicatorTypeEnum.POSITIVE, "Permite que el cliente termine sus frases.", None),
            (IndicatorTypeEnum.NEGATIVE, "Interrumpe al cliente de manera recurrente.", None),
            (IndicatorTypeEnum.NEGATIVE, "Responde sin haber entendido la necesidad real.", None),
        ],
    },
    {
        "code": "NEED_IDENTIFICATION",
        "name": "Identificación de la Necesidad",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador identifica correctamente la necesidad o problema "
            "real del cliente antes de proponer una solución."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.5,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.RELIABILITY", "FORRESTER.EFFECTIVENESS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Hace preguntas aclaratorias relevantes.", "podría decirme|me puede confirmar|para entender mejor"),
            (IndicatorTypeEnum.NEGATIVE, "Asume la necesidad sin verificar con el cliente.", None),
        ],
    },
    {
        "code": "CLEAR_COMMUNICATION",
        "name": "Claridad en la Comunicación",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador comunica información de manera clara, precisa y "
            "adaptada al nivel de comprensión del cliente."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.2,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.RELIABILITY", "FORRESTER.EASE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Explica en términos sencillos sin jerga innecesaria.", None),
            (IndicatorTypeEnum.POSITIVE, "Confirma que el cliente entendió la información.", None),
            (IndicatorTypeEnum.NEGATIVE, "Usa tecnicismos sin explicación que confunden al cliente.", None),
        ],
    },
    {
        "code": "EMPATHY_DEMONSTRATION",
        "name": "Demostración de Empatía",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador demuestra empatía explícita reconociendo el "
            "estado emocional del cliente y validando su sentir."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.3,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.EMPATHY", "FORRESTER.EMOTION"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Reconoce verbalmente la emoción del cliente.", "entiendo su|comprendo que|lamento que"),
            (IndicatorTypeEnum.POSITIVE, "Adapta el tono al estado emocional del cliente.", None),
            (IndicatorTypeEnum.NEGATIVE, "Ignora señales evidentes de molestia o frustración.", None),
        ],
    },
    {
        "code": "PROFESSIONAL_TONE",
        "name": "Tono Profesional",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador mantiene tono y vocabulario profesional durante "
            "toda la interacción, incluso bajo presión."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.ASSURANCE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Usa vocabulario respetuoso y apropiado.", None),
            (IndicatorTypeEnum.NEGATIVE, "Pierde el control del tono ante clientes molestos.", None),
            (IndicatorTypeEnum.NEGATIVE, "Usa muletillas o vocabulario informal/inapropiado.", None),
        ],
    },
    {
        "code": "KNOWLEDGE_ACCURACY",
        "name": "Exactitud del Conocimiento",
        "category": CompetencyCategoryEnum.ATTENTION,
        "definition": (
            "El colaborador demuestra conocimiento técnico y de producto "
            "correcto, sin dar información falsa o imprecisa."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.2,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.ASSURANCE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Responde con precisión sobre productos y procesos.", None),
            (IndicatorTypeEnum.POSITIVE, "Admite honestamente cuando no sabe y busca apoyo.", "permítame verificar|déjeme consultar"),
            (IndicatorTypeEnum.NEGATIVE, "Entrega información incorrecta o contradictoria.", None),
        ],
    },

    # ---------- RESOLUTION ----------
    {
        "code": "PROBLEM_RESOLUTION",
        "name": "Resolución del Problema",
        "category": CompetencyCategoryEnum.RESOLUTION,
        "definition": (
            "El colaborador resuelve efectivamente el problema o necesidad "
            "del cliente dentro de sus capacidades."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 2.0,
        "ai_field_hint": "problem_resolved",
        "framework_refs": ["SERVQUAL.RELIABILITY", "FORRESTER.EFFECTIVENESS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "El cliente confirma que su necesidad fue atendida.", None),
            (IndicatorTypeEnum.NEGATIVE, "La interacción termina sin resolución y sin plan claro.", None),
        ],
    },
    {
        "code": "FIRST_CONTACT_RESOLUTION",
        "name": "Resolución en Primer Contacto",
        "category": CompetencyCategoryEnum.RESOLUTION,
        "definition": (
            "La necesidad del cliente se resuelve en el primer contacto, "
            "sin requerir rellamadas o seguimientos."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.5,
        "ai_field_hint": None,
        "framework_refs": ["COPC.FCR", "FORRESTER.EASE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "No se compromete con rellamada ni traslado del caso.", None),
            (IndicatorTypeEnum.NEGATIVE, "Solicita al cliente que vuelva a llamar o escribir.", None),
        ],
    },
    {
        "code": "ALTERNATIVE_OFFERING",
        "name": "Ofrecimiento de Alternativas",
        "category": CompetencyCategoryEnum.RESOLUTION,
        "definition": (
            "Cuando no hay solución inmediata, el colaborador ofrece "
            "alternativas razonables al cliente."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.RESPONSIVENESS", "FORRESTER.EFFECTIVENESS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Propone 2+ alternativas cuando la opción principal no aplica.", None),
            (IndicatorTypeEnum.NEGATIVE, "Responde 'no se puede' sin explorar alternativas.", None),
        ],
    },
    {
        "code": "ESCALATION_HANDLING",
        "name": "Manejo de Escalamiento",
        "category": CompetencyCategoryEnum.RESOLUTION,
        "definition": (
            "Cuando el caso excede sus capacidades, el colaborador escala "
            "de forma ordenada con transferencia clara de contexto."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["ISO10002.COMPLAINT_HANDLING"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Explica al cliente el motivo del escalamiento y próximos pasos.", None),
            (IndicatorTypeEnum.NEGATIVE, "Transfiere al cliente sin avisar ni contextualizar al siguiente agente.", None),
        ],
    },

    # ---------- VALUE ----------
    {
        "code": "PRODUCT_OFFERING",
        "name": "Ofrecimiento de Productos/Servicios",
        "category": CompetencyCategoryEnum.VALUE,
        "definition": (
            "El colaborador identifica y ofrece proactivamente productos o "
            "servicios adicionales relevantes para el cliente."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": "product_offered",
        "framework_refs": ["KANO.ATTRACTIVE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Ofrece producto relevante basado en la necesidad del cliente.", None),
            (IndicatorTypeEnum.NEGATIVE, "Detecta oportunidad clara pero no la aprovecha.", None),
        ],
    },
    {
        "code": "CROSS_SELL",
        "name": "Venta Cruzada",
        "category": CompetencyCategoryEnum.VALUE,
        "definition": (
            "El colaborador propone productos complementarios pertinentes, "
            "sin presionar."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 0.8,
        "ai_field_hint": None,
        "framework_refs": ["KANO.ATTRACTIVE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Sugiere producto complementario natural al contexto.", None),
            (IndicatorTypeEnum.NEGATIVE, "Presiona al cliente con ventas irrelevantes.", None),
        ],
    },
    {
        "code": "PROACTIVE_INFORMATION",
        "name": "Información Proactiva",
        "category": CompetencyCategoryEnum.VALUE,
        "definition": (
            "El colaborador entrega información útil no solicitada que "
            "anticipa necesidades del cliente."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 0.8,
        "ai_field_hint": None,
        "framework_refs": ["KANO.ATTRACTIVE", "FORRESTER.EMOTION"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Comparte información útil adicional al motivo del contacto.", None),
            (IndicatorTypeEnum.NEGATIVE, "Se limita estrictamente al motivo del contacto sin valor añadido.", None),
        ],
    },

    # ---------- EFFORT ----------
    {
        "code": "LOW_EFFORT_INTERACTION",
        "name": "Interacción de Bajo Esfuerzo",
        "category": CompetencyCategoryEnum.EFFORT,
        "definition": (
            "El cliente logra su objetivo con el menor esfuerzo posible."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.5,
        "ai_field_hint": None,
        "framework_refs": ["CES.EFFORT", "FORRESTER.EASE"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "El cliente logra su objetivo sin obstáculos.", None),
            (IndicatorTypeEnum.NEGATIVE, "Múltiples obstáculos o pasos innecesarios para el cliente.", None),
        ],
    },
    {
        "code": "NO_REPETITION",
        "name": "Sin Repetición de Información",
        "category": CompetencyCategoryEnum.EFFORT,
        "definition": (
            "El cliente no tiene que repetir información ya proporcionada."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["CES.EFFORT", "COPC.QUALITY"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Usa datos ya disponibles sin repreguntar.", None),
            (IndicatorTypeEnum.NEGATIVE, "Pide al cliente repetir datos ya compartidos.", None),
        ],
    },
    {
        "code": "REASONABLE_WAIT_TIME",
        "name": "Tiempo de Espera Razonable",
        "category": CompetencyCategoryEnum.EFFORT,
        "definition": (
            "Los tiempos de espera, silencios o pausas durante la interacción "
            "son razonables para el contexto."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["ISO18295.CONTACT_REQUIREMENTS", "COPC.AHT"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Las esperas son breves y están justificadas verbalmente.", "un momento|deme un segundo|permítame"),
            (IndicatorTypeEnum.NEGATIVE, "Silencios prolongados sin aviso al cliente.", None),
        ],
    },

    # ---------- CLOSURE ----------
    {
        "code": "CLOSURE_STANDARD",
        "name": "Cierre Estándar",
        "category": CompetencyCategoryEnum.CLOSURE,
        "definition": (
            "El colaborador cierra la interacción con protocolo apropiado: "
            "agradecimiento y despedida cordial."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["ISO18295.CONTACT_REQUIREMENTS", "SERVQUAL.RESPONSIVENESS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Agradece la interacción y se despide cordialmente.", "gracias por|que tenga|feliz"),
            (IndicatorTypeEnum.NEGATIVE, "Termina la interacción abruptamente sin despedida.", None),
        ],
    },
    {
        "code": "CONFIRMATION_OF_RESOLUTION",
        "name": "Confirmación de Resolución",
        "category": CompetencyCategoryEnum.CLOSURE,
        "definition": (
            "El colaborador confirma explícitamente con el cliente que su "
            "necesidad fue satisfecha antes de cerrar."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.2,
        "ai_field_hint": None,
        "framework_refs": ["FORRESTER.EFFECTIVENESS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Pregunta directamente si hay algo más en que pueda ayudar.", "algo más|alguna otra consulta|puedo ayudarle en algo"),
            (IndicatorTypeEnum.NEGATIVE, "Cierra sin validar si la necesidad quedó cubierta.", None),
        ],
    },
    {
        "code": "NEXT_STEPS_COMMUNICATION",
        "name": "Comunicación de Próximos Pasos",
        "category": CompetencyCategoryEnum.CLOSURE,
        "definition": (
            "Cuando la interacción requiere acción posterior, el colaborador "
            "comunica con claridad los próximos pasos, responsables y plazos."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.RELIABILITY"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Indica qué sigue, quién hace qué y cuándo.", None),
            (IndicatorTypeEnum.NEGATIVE, "Deja al cliente sin saber cómo continúa su caso.", None),
        ],
    },

    # ---------- COMPLIANCE_EMOTIONAL ----------
    {
        "code": "CUSTOMER_EMOTION_TRACKING",
        "name": "Seguimiento del Estado Emocional del Cliente",
        "category": CompetencyCategoryEnum.COMPLIANCE_EMOTIONAL,
        "definition": (
            "El colaborador detecta y adapta su comportamiento al estado "
            "emocional del cliente a lo largo de la interacción."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.0,
        "ai_field_hint": "customer_emotion",
        "framework_refs": ["FORRESTER.EMOTION", "SERVQUAL.EMPATHY"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Adapta el lenguaje y tono según emoción detectada.", None),
            (IndicatorTypeEnum.NEGATIVE, "Mantiene tono neutro aunque el cliente muestre frustración evidente.", None),
        ],
    },
    {
        "code": "COMPLAINT_HANDLING",
        "name": "Manejo Adecuado de Quejas",
        "category": CompetencyCategoryEnum.COMPLIANCE_EMOTIONAL,
        "definition": (
            "El colaborador gestiona quejas siguiendo principios de "
            "reconocimiento, disculpa genuina, solución y seguimiento."
        ),
        "measurement_type": CompetencyMeasurementType.LIKERT,
        "default_weight": 1.2,
        "ai_field_hint": None,
        "framework_refs": ["ISO10002.COMPLAINT_HANDLING"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Reconoce el problema y ofrece disculpa genuina.", "lamento|disculpe|lo sentimos"),
            (IndicatorTypeEnum.POSITIVE, "Propone plan de acción con seguimiento.", None),
            (IndicatorTypeEnum.NEGATIVE, "Minimiza o justifica la queja del cliente.", None),
        ],
    },
    {
        "code": "DATA_PRIVACY_COMPLIANCE",
        "name": "Cumplimiento de Privacidad de Datos",
        "category": CompetencyCategoryEnum.COMPLIANCE_EMOTIONAL,
        "definition": (
            "El colaborador maneja datos personales del cliente conforme a "
            "protocolos de privacidad y confidencialidad."
        ),
        "measurement_type": CompetencyMeasurementType.BOOLEAN,
        "default_weight": 1.0,
        "ai_field_hint": None,
        "framework_refs": ["SERVQUAL.ASSURANCE", "ISO18295.CONTACT_REQUIREMENTS"],
        "indicators": [
            (IndicatorTypeEnum.POSITIVE, "Verifica identidad del cliente antes de compartir información sensible.", None),
            (IndicatorTypeEnum.NEGATIVE, "Comparte datos sensibles sin verificación de identidad.", None),
        ],
    },
]


# Templates por industria: qué competencias aplican, peso y obligatoriedad.
# Formato: { industry_code: [ (competency_code, suggested_weight, is_mandatory), ... ] }
# Si una competencia no aparece en la lista de una industria, no forma parte
# del template inicial (pero la empresa puede agregarla manualmente).

_ALL_COMPETENCY_CODES = [c["code"] for c in COMPETENCIES]


def _default_industry_template(
    mandatory_codes: List[str],
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[str, float, bool]]:
    """Construye un template que incluye todas las competencias.

    - `mandatory_codes`: lista de competencias obligatorias para la industria.
    - `weights`: override de pesos por competencia (opcional).
    """
    w = weights or {}
    out: List[Tuple[str, float, bool]] = []
    for code in _ALL_COMPETENCY_CODES:
        suggested = w.get(code, 1.0)
        out.append((code, suggested, code in mandatory_codes))
    return out


INDUSTRY_TEMPLATES: Dict[str, List[Tuple[str, float, bool]]] = {
    "BANCA": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "AGENT_IDENTIFICATION",
            "DATA_PRIVACY_COMPLIANCE",
            "KNOWLEDGE_ACCURACY",
            "PROBLEM_RESOLUTION",
            "CLOSURE_STANDARD",
        ],
        weights={
            "DATA_PRIVACY_COMPLIANCE": 2.0,
            "KNOWLEDGE_ACCURACY": 1.5,
            "PROBLEM_RESOLUTION": 2.0,
            "COMPLAINT_HANDLING": 1.5,
        },
    ),
    "RETAIL": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "ACTIVE_LISTENING",
            "PRODUCT_OFFERING",
            "CLOSURE_STANDARD",
        ],
        weights={
            "PRODUCT_OFFERING": 1.5,
            "CROSS_SELL": 1.2,
            "PROACTIVE_INFORMATION": 1.2,
        },
    ),
    "SALUD": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "AGENT_IDENTIFICATION",
            "EMPATHY_DEMONSTRATION",
            "DATA_PRIVACY_COMPLIANCE",
            "COMPLAINT_HANDLING",
            "CLOSURE_STANDARD",
        ],
        weights={
            "EMPATHY_DEMONSTRATION": 2.0,
            "DATA_PRIVACY_COMPLIANCE": 2.0,
            "COMPLAINT_HANDLING": 1.5,
            "CUSTOMER_EMOTION_TRACKING": 1.5,
        },
    ),
    "TELCO": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "AGENT_IDENTIFICATION",
            "FIRST_CONTACT_RESOLUTION",
            "NO_REPETITION",
            "CLOSURE_STANDARD",
        ],
        weights={
            "FIRST_CONTACT_RESOLUTION": 2.0,
            "LOW_EFFORT_INTERACTION": 1.5,
            "NO_REPETITION": 1.5,
            "PROBLEM_RESOLUTION": 1.8,
        },
    ),
    "HORECA": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "EMPATHY_DEMONSTRATION",
            "PROACTIVE_INFORMATION",
            "CLOSURE_STANDARD",
        ],
        weights={
            "EMPATHY_DEMONSTRATION": 1.5,
            "PROACTIVE_INFORMATION": 1.5,
            "CUSTOMER_EMOTION_TRACKING": 1.3,
            "PRODUCT_OFFERING": 1.2,
        },
    ),
    "SEGUROS": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "AGENT_IDENTIFICATION",
            "KNOWLEDGE_ACCURACY",
            "COMPLAINT_HANDLING",
            "DATA_PRIVACY_COMPLIANCE",
            "CLOSURE_STANDARD",
        ],
        weights={
            "COMPLAINT_HANDLING": 2.0,
            "KNOWLEDGE_ACCURACY": 1.8,
            "CLEAR_COMMUNICATION": 1.5,
        },
    ),
    "EDUCACION": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "CLEAR_COMMUNICATION",
            "EMPATHY_DEMONSTRATION",
            "CLOSURE_STANDARD",
        ],
        weights={
            "CLEAR_COMMUNICATION": 1.8,
            "EMPATHY_DEMONSTRATION": 1.5,
            "PROACTIVE_INFORMATION": 1.3,
        },
    ),
    "GOBIERNO": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "CLEAR_COMMUNICATION",
            "COMPLAINT_HANDLING",
            "DATA_PRIVACY_COMPLIANCE",
            "CLOSURE_STANDARD",
        ],
        weights={
            "LOW_EFFORT_INTERACTION": 1.8,
            "COMPLAINT_HANDLING": 1.5,
            "CLEAR_COMMUNICATION": 1.5,
            "NO_REPETITION": 1.3,
        },
    ),
    "LOGISTICA": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "PROBLEM_RESOLUTION",
            "COMPLAINT_HANDLING",
            "CLOSURE_STANDARD",
        ],
        weights={
            "FIRST_CONTACT_RESOLUTION": 1.5,
            "LOW_EFFORT_INTERACTION": 1.5,
            "COMPLAINT_HANDLING": 1.8,
            "PROBLEM_RESOLUTION": 1.8,
        },
    ),
    "TURISMO": _default_industry_template(
        mandatory_codes=[
            "GREETING_STANDARD",
            "EMPATHY_DEMONSTRATION",
            "PROACTIVE_INFORMATION",
            "CLOSURE_STANDARD",
        ],
        weights={
            "EMPATHY_DEMONSTRATION": 1.5,
            "PROACTIVE_INFORMATION": 1.8,
            "CUSTOMER_EMOTION_TRACKING": 1.5,
            "PRODUCT_OFFERING": 1.3,
        },
    ),
}


# =============================================================================
# Lógica del seeder (idempotente)
# =============================================================================

async def _get_or_create_industry(session: AsyncSession, data: Dict) -> Industry:
    stmt = select(Industry).where(Industry.code == data["code"])
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing
    obj = Industry(
        code=data["code"],
        name=data["name"],
        description=data.get("description"),
        icon=data.get("icon"),
        is_active=True,
    )
    session.add(obj)
    await session.flush()
    logger.info("Industry created: %s", obj.code)
    return obj


async def _get_or_create_framework(session: AsyncSession, data: Dict) -> Framework:
    stmt = select(Framework).where(Framework.code == data["code"])
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing
    obj = Framework(
        code=data["code"],
        name=data["name"],
        authors=data.get("authors"),
        year=data.get("year"),
        source_citation=data.get("source_citation"),
        url_reference=data.get("url_reference"),
        description=data.get("description"),
        is_active=True,
    )
    session.add(obj)
    await session.flush()
    logger.info("Framework created: %s", obj.code)
    return obj


async def _get_or_create_dimension(
    session: AsyncSession,
    framework_id: int,
    code: str,
    name: str,
    description: Optional[str],
    order: int,
) -> FrameworkDimension:
    stmt = select(FrameworkDimension).where(FrameworkDimension.code == code)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing
    obj = FrameworkDimension(
        framework_id=framework_id,
        code=code,
        name=name,
        description=description,
        order=order,
    )
    session.add(obj)
    await session.flush()
    logger.info("FrameworkDimension created: %s", obj.code)
    return obj


async def _get_or_create_competency(
    session: AsyncSession, data: Dict
) -> QualityCompetency:
    stmt = select(QualityCompetency).where(QualityCompetency.code == data["code"])
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing
    obj = QualityCompetency(
        code=data["code"],
        name=data["name"],
        category=data["category"],
        definition=data.get("definition"),
        measurement_type=data["measurement_type"],
        default_weight=data["default_weight"],
        ai_field_hint=data.get("ai_field_hint"),
        is_active=True,
    )
    session.add(obj)
    await session.flush()
    logger.info("QualityCompetency created: %s", obj.code)
    return obj


async def _ensure_indicator(
    session: AsyncSession,
    competency_id: int,
    indicator_type: IndicatorTypeEnum,
    description: str,
    detection_hint: Optional[str],
    order: int,
) -> None:
    stmt = select(CompetencyIndicator).where(
        CompetencyIndicator.competency_id == competency_id,
        CompetencyIndicator.description == description,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return
    obj = CompetencyIndicator(
        competency_id=competency_id,
        indicator_type=indicator_type,
        description=description,
        detection_hint=detection_hint,
        order=order,
    )
    session.add(obj)


async def _ensure_framework_ref(
    session: AsyncSession, competency_id: int, dimension_id: int
) -> None:
    stmt = select(CompetencyFrameworkRef).where(
        CompetencyFrameworkRef.competency_id == competency_id,
        CompetencyFrameworkRef.framework_dimension_id == dimension_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return
    obj = CompetencyFrameworkRef(
        competency_id=competency_id,
        framework_dimension_id=dimension_id,
    )
    session.add(obj)


async def _ensure_industry_template_item(
    session: AsyncSession,
    industry_id: int,
    competency_id: int,
    suggested_weight: float,
    is_mandatory: bool,
) -> None:
    stmt = select(IndustryTemplate).where(
        IndustryTemplate.industry_id == industry_id,
        IndustryTemplate.competency_id == competency_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return
    obj = IndustryTemplate(
        industry_id=industry_id,
        competency_id=competency_id,
        suggested_weight=suggested_weight,
        is_mandatory=is_mandatory,
    )
    session.add(obj)


async def seed_quality_framework(session: AsyncSession) -> Dict[str, int]:
    """Ejecuta el seeder completo. Retorna conteos para reporte."""
    stats = {
        "industries": 0,
        "frameworks": 0,
        "dimensions": 0,
        "competencies": 0,
        "indicators": 0,
        "framework_refs": 0,
        "industry_template_items": 0,
    }

    # 1) Industrias
    industries_by_code: Dict[str, Industry] = {}
    for ind_data in INDUSTRIES:
        ind = await _get_or_create_industry(session, ind_data)
        industries_by_code[ind.code] = ind
        stats["industries"] += 1

    # 2) Frameworks y dimensiones
    dimensions_by_code: Dict[str, FrameworkDimension] = {}
    for fw_data in FRAMEWORKS:
        fw = await _get_or_create_framework(session, fw_data)
        stats["frameworks"] += 1
        for code, name, desc, order in fw_data["dimensions"]:
            dim = await _get_or_create_dimension(
                session, fw.id, code, name, desc, order
            )
            dimensions_by_code[code] = dim
            stats["dimensions"] += 1

    # 3) Competencias + indicadores + framework_refs
    competencies_by_code: Dict[str, QualityCompetency] = {}
    for comp_data in COMPETENCIES:
        comp = await _get_or_create_competency(session, comp_data)
        competencies_by_code[comp.code] = comp
        stats["competencies"] += 1

        for order, (ind_type, desc, hint) in enumerate(comp_data.get("indicators", [])):
            await _ensure_indicator(
                session, comp.id, ind_type, desc, hint, order
            )
            stats["indicators"] += 1

        for dim_code in comp_data.get("framework_refs", []):
            dim = dimensions_by_code.get(dim_code)
            if not dim:
                logger.warning(
                    "Framework dimension not found: %s (referenced by %s)",
                    dim_code,
                    comp.code,
                )
                continue
            await _ensure_framework_ref(session, comp.id, dim.id)
            stats["framework_refs"] += 1

    await session.flush()

    # 4) Templates por industria
    for ind_code, items in INDUSTRY_TEMPLATES.items():
        industry = industries_by_code.get(ind_code)
        if not industry:
            logger.warning("Industry not found for template: %s", ind_code)
            continue
        for comp_code, suggested_weight, is_mandatory in items:
            comp = competencies_by_code.get(comp_code)
            if not comp:
                logger.warning(
                    "Competency not found for template %s: %s", ind_code, comp_code
                )
                continue
            await _ensure_industry_template_item(
                session, industry.id, comp.id, suggested_weight, is_mandatory
            )
            stats["industry_template_items"] += 1

    await session.commit()
    return stats


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    async with AsyncSessionLocal() as session:
        stats = await seed_quality_framework(session)
    logger.info("Seed completed. Stats: %s", stats)
    print("Quality Framework seed completed:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
