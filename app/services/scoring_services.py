# app/services/scoring_services.py
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.survey_forms_model import SurveyForm
from app.models.survey_model import SurveySection, SurveyAspect
from app.models.campaign_model import Campaign

class ScoringError(Exception):
    pass

async def _get_form_by_campaign(session: AsyncSession, campaign_id: int) -> SurveyForm | None:
    # Campaign has relationship to survey (survey_forms). Try join.
    q = select(SurveyForm).join(Campaign, Campaign.survey_id == SurveyForm.id) \
        .where(Campaign.id == campaign_id, SurveyForm.deleted_at == None)
    res = await session.execute(q)
    return res.scalars().first()

async def load_form(session: AsyncSession, campaign_id: int) -> SurveyForm:
    form = await _get_form_by_campaign(session, campaign_id)
    if not form:
        raise ScoringError(f"No survey form linked to campaign {campaign_id}")
    # ensure sections/aspects are loaded (you can rely on relationships lazy load if configured)
    # We'll query sections+aspects to be safe
    q = select(SurveySection).where(SurveySection.form_id == form.id, SurveySection.deleted_at == None)
    res = await session.execute(q)
    sections = res.scalars().all()
    # attach aspects per section
    for s in sections:
        q2 = select(SurveyAspect).where(SurveyAspect.section_id == s.id, SurveyAspect.deleted_at == None).order_by(SurveyAspect.order)
        r2 = await session.execute(q2)
        s.aspects = r2.scalars().all()
    form.sections = sections
    return form

def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

async def calculate_evaluation_scores(
    session: AsyncSession,
    campaign_id: int,
    answers: List[dict],
) -> Dict[str, Any]:
    """
    answers: list of dicts with keys: aspect_id, value_number (opt), value_boolean (opt)
    Returns a structure with per-aspect awarded points, per-section totals and global totals.
    """
    form = await load_form(session, campaign_id)

    # Map aspects by id
    aspect_map = {}
    section_map = {}
    for section in form.sections:
        section_map[section.id] = {
            "section_id": section.id,
            "section_name": section.name,
            "section_max": float(section.maximum_score or 0),
            "aspects": {}
        }
        n_aspects = max(1, len(section.aspects))
        # computed per-aspect weight = section_max / n_aspects (lineal)
        per_aspect = section_map[section.id]["section_max"] / n_aspects
        for aspect in section.aspects:
            aspect.maximum_score = float(aspect.maximum_score) if aspect.maximum_score is not None else per_aspect
            # The authoritative maximum for scoring is aspect.maximum_score (we assume create/update form stored it)
            aspect_map[aspect.id] = {
                "aspect_id": aspect.id,
                "section_id": section.id,
                "aspect_max": float(aspect.maximum_score),
                "type": aspect.type.value if hasattr(aspect.type, "value") else aspect.type,
                "description": getattr(aspect, "description", ""),
                "per_aspect": per_aspect
            }
            section_map[section.id]["aspects"][aspect.id] = aspect_map[aspect.id]

    # Prepare results containers
    sections_result: Dict[int, Dict] = {}
    total_possible = 0.0
    total_awarded = 0.0

    # initialize section results
    for sid, s in section_map.items():
        sections_result[sid] = {
            "section_id": sid,
            "section_name": s["section_name"],
            "section_max": s["section_max"],
            "section_awarded": 0.0,
            "aspects": {}
        }
        total_possible += s["section_max"]

    # compute per answer
    for ans in answers:
        aspect_id = ans.get("aspect_id")
        if aspect_id not in aspect_map:
            raise ScoringError(f"Answer references unknown aspect_id {aspect_id}")

        a = aspect_map[aspect_id]
        section_id = a["section_id"]
        aspect_max = a["aspect_max"]
        aspect_type = a["type"]

        awarded = 0.0

        if aspect_type == "boolean" or aspect_type == "BOOLEAN" or aspect_type == "boolean":
            val_bool = ans.get("value_boolean")
            # if boolean True -> awarded = aspect_max else 0
            if val_bool:
                awarded = float(aspect_max)
            else:
                awarded = 0.0
        else:
            # number type
            val_num = ans.get("value_number")
            if val_num is None:
                # if no numeric provided, treat as 0
                awarded = 0.0
            else:
                vn = _safe_float(val_num)
                # Validate: cannot exceed aspect_max
                if vn > aspect_max + 1e-9:
                    # strict: error to surface to API
                    raise ScoringError(f"Numeric answer for aspect {aspect_id} ({vn}) exceeds maximum {aspect_max}")
                awarded = vn

        # accumulate
        sections_result[section_id]["aspects"][aspect_id] = {
            "aspect_id": aspect_id,
            "aspect_max": aspect_max,
            "awarded": awarded
        }
        sections_result[section_id]["section_awarded"] += awarded
        total_awarded += awarded

    # finalize
    percentage = (total_awarded / total_possible * 100.0) if total_possible > 0 else 0.0

    return {
        "form_id": form.id,
        "total_possible": total_possible,
        "total_awarded": total_awarded,
        "percentage": percentage,
        "sections": sections_result,
    }
