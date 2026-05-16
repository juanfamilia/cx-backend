"""Heurísticas de recorrido participante — paridad funcional con Angular `participant-journey-preview.helper`.

Sin LLM: solo texto existente en spec + brief.
"""

from __future__ import annotations

import re
from typing import Any

from app.study_intelligence.contracts import JourneyPhase

_PHASE_DEFS: tuple[dict[str, str], ...] = (
    {
        "id": "intro",
        "title": "Introducción",
        "base_narrative": "Por qué participa y qué va a pasar, en pocos minutos claros.",
        "base_objective": "Generar confianza y contexto antes de preguntas sustantivas.",
    },
    {
        "id": "screening",
        "title": "Selección",
        "base_narrative": "Confirmar que encaja con quién necesita oír, sin alargarse.",
        "base_objective": "Asegurar que las respuestas aplican al público correcto.",
    },
    {
        "id": "experience",
        "title": "Experiencia central",
        "base_narrative": "El momento del estudio: lo vivido, recordado o evaluado.",
        "base_objective": "Capturar lo que importa para la decisión de negocio.",
    },
    {
        "id": "satisfaction",
        "title": "Valoración",
        "base_narrative": "Impresión general ya con la experiencia fresca.",
        "base_objective": "Sintetizar actitud o satisfacción sin adelantar el relato.",
    },
    {
        "id": "demographics",
        "title": "Perfil",
        "base_narrative": "Datos de perfil; suele funcionar mejor después del tema central.",
        "base_objective": "Completar segmentación sin cansar antes de tiempo.",
    },
    {
        "id": "close",
        "title": "Cierre",
        "base_narrative": "Agradecimiento claro y salida limpia.",
        "base_objective": "Dejar una sensación respetuosa y profesional.",
    },
)


def phase_index_for_block_title(title: str) -> int:
    """Índice de fase 0..5 según título de bloque; -1 si no coincide."""
    t = title.lower()
    tests: tuple[tuple[int, tuple[str, ...]], ...] = (
        (0, ("intro", "bienven", "contexto", "propósito", "proposito", "calibr")),
        (1, ("screen", "filt", "elegib", "cuota", "recruit", "target")),
        (
            2,
            ("experien", "jornada", "uso", "touch", "compra", "visita", "interacc", "onboarding"),
        ),
        (3, ("satisf", "nps", "csat", "recomen", "valoración", "valoracion")),
        (4, ("demográf", "demograf", "socio", "edad", "género", "genero", "ingreso", "perfil")),
        (5, ("cierre", "desped", "thank", "gracia", "final")),
    )
    for i, keys in tests:
        if any(k in t for k in keys):
            return i
    return -1


def extract_block_pairs(spec: dict[str, Any]) -> list[tuple[str | None, str]]:
    """Pares (block_id, título) desde blocks | sections | pages | items."""
    arr: list[Any] | None = None
    for k in ("blocks", "sections", "pages", "items"):
        v = spec.get(k)
        if isinstance(v, list) and len(v) > 0:
            arr = v
            break
    if arr is None:
        return []
    out: list[tuple[str | None, str]] = []
    for i, raw in enumerate(arr[:48]):
        if not isinstance(raw, dict):
            continue
        bid = raw.get("block_id")
        bid_str = str(bid) if bid is not None else None
        tv = raw.get("title") or raw.get("name") or raw.get("label") or raw.get("heading")
        title = tv.strip() if isinstance(tv, str) else ""
        if not title:
            title = f"Momento {i + 1}"
        out.append((bid_str, title))
    return out


def trim_join_brief(payload: dict[str, Any], guided: dict[str, str]) -> str:
    chunks = [
        guided.get("guided_objective", ""),
        guided.get("guided_business_question", ""),
        guided.get("guided_audience", ""),
        guided.get("guided_market", ""),
        guided.get("guided_expected_outcome", ""),
    ]
    blob = " ".join(s.strip().lower() for s in chunks if isinstance(s, str) and s.strip())
    keys = ("methodology", "study_type", "hypothesis", "constraints", "notes")
    parts: list[str] = []
    for k in keys:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    extra = " ".join(parts).lower()
    return f"{blob} {extra}".strip()


def extract_guided_strings(payload: dict[str, Any]) -> dict[str, str]:
    """Campos guiados en snake_case dentro del payload si existen."""
    keys = (
        "guided_objective",
        "guided_business_question",
        "guided_audience",
        "guided_market",
        "guided_expected_outcome",
    )
    return {k: str(payload[k]).strip() for k in keys if isinstance(payload.get(k), str)}


def infer_sensitive_topic_hint(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(
        r"onboarding|cuenta|banco|cr[eé]dito|pr[eé]stamo|dinero|tarjeta|fraude",
        blob,
        re.I,
    ):
        return (
            "Temas financieros suelen pedir tono calmado y pocas preguntas sensibles seguidas."
        )
    if re.search(r"salud|clínica|medic|paciente|diagn", blob, re.I):
        return "Salud y bienestar suelen requerir especial cuidado en redacción y ritmo."
    if re.search(r"emplead|rrhh|evaluación laboral|encuesta interna", blob, re.I):
        return "Temas laborales pueden generar cautela: claridad y anonimato ayudan."
    return None


def demographics_early(block_pairs: list[tuple[str | None, str]]) -> bool:
    titles = [t for _, t in block_pairs]
    n = len(titles)
    if n < 4:
        return False
    half = n // 2
    for idx, title in enumerate(titles):
        if phase_index_for_block_title(title) == 4 and idx < half:
            return True
    return False


def early_positive_lean(block_pairs: list[tuple[str | None, str]]) -> bool:
    titles = [t for _, t in block_pairs]
    if len(titles) < 6:
        return False
    half_slice = titles[: max(1, (len(titles) + 1) // 2)]
    for t in half_slice:
        x = t.lower()
        if "satisf" in x or "excelente" in x or "maravill" in x:
            return True
    return False


def build_journey_phases(spec: dict[str, Any], brief_blob: str) -> tuple[tuple[JourneyPhase, ...], dict[str, Any]]:
    """Devuelve fases + flags heurísticos para fatiga/insights."""
    pairs = extract_block_pairs(spec)
    has_instrument = len(pairs) > 0
    counts = [0, 0, 0, 0, 0, 0]
    bucket_ids: list[list[str]] = [[] for _ in range(6)]
    rr = 0
    for bid, title in pairs:
        ix = phase_index_for_block_title(title)
        if ix < 0:
            ix = rr % 6
            rr += 1
        counts[ix] += 1
        if bid:
            bucket_ids[ix].append(bid)

    total = len(pairs)
    demo_early = demographics_early(pairs)
    induced_early = early_positive_lean(pairs)
    heavy_survey = total >= 9
    exp_heavy = counts[2] >= 4 or (heavy_survey and counts[2] >= 2)
    sensitive_hint = infer_sensitive_topic_hint(brief_blob)

    phases: list[JourneyPhase] = []
    for phase_ix, defn in enumerate(_PHASE_DEFS):
        mapped_blocks = counts[phase_ix]
        bids = tuple(bucket_ids[phase_ix])
        base_n = defn["base_narrative"]
        if not has_instrument and len(brief_blob) > 30:
            narrative = f"{base_n} Su brief ya orienta el tono; falta reflejarlo en bloques del instrumento."
        else:
            narrative = base_n

        if mapped_blocks > 0:
            narrative_summary = (
                f"{narrative} ({mapped_blocks} bloque{'s' if mapped_blocks != 1 else ''} "
                f"reconocido{'s' if mapped_blocks != 1 else ''} en esta etapa.)"
            )
        else:
            narrative_summary = narrative

        if has_instrument and mapped_blocks == 0:
            narrative_summary = (
                f"{narrative} Todavía no hay bloques claros en esta parte del borrador; "
                "puede añadirlos o renombrarlos para alinear el relato."
            )

        phases.append(
            JourneyPhase(
                phase_key=defn["id"],
                order_index=phase_ix,
                title=defn["title"],
                narrative_summary=narrative_summary,
                block_ids=bids,
            )
        )

    flags = {
        "has_instrument": has_instrument,
        "total_blocks": total,
        "counts": counts,
        "demo_early": demo_early,
        "induced_early": induced_early,
        "heavy_survey": heavy_survey,
        "exp_heavy": exp_heavy,
        "sensitive_hint": sensitive_hint,
    }
    return tuple(phases), flags
