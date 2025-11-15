# app/services/survey_forms_services.py (modificar create_survey_form y update_survey_form)

from datetime import datetime
from typing import Optional
from fastapi import Query
from sqlmodel import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company_model import Company
from app.models.survey_forms_model import (
    SurveyForm,
    SurveyFormPublic,
    SurveyFormsCreate,
    SurveyFormsPublic,
)
from app.models.survey_model import (
    SurveySection,
    SurveyAspect,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException, PermissionDeniedException

# ... (otros métodos no mostrados) ...

async def _distribute_aspect_weights(session: AsyncSession, form: SurveyForm):
    """
    For each section in form, set each aspect.maximum_score = section.maximum_score / n_aspects
    and persist those changes (overwriting any manual aspect.maximum_score).
    """
    # load sections and aspects
    q = select(SurveySection).where(SurveySection.form_id == form.id, SurveySection.deleted_at == None)
    res = await session.execute(q)
    sections = res.scalars().all()
    for s in sections:
        q2 = select(SurveyAspect).where(SurveyAspect.section_id == s.id, SurveyAspect.deleted_at == None).order_by(SurveyAspect.order)
        r2 = await session.execute(q2)
        aspects = r2.scalars().all()
        n = len(aspects)
        if n == 0:
            continue
        per = float(s.maximum_score) / n
        for asp in aspects:
            asp.maximum_score = int(per) if per.is_integer() else per
            session.add(asp)
    # no commit here; caller will commit

async def create_survey_form(
    session: AsyncSession, company_id: int, data: SurveyFormsCreate
) -> SurveyForm:

    # Validate sum of section maximums == 100
    total_sections = sum([sec.maximum_score for sec in data.sections])
    if abs(total_sections - 100.0) > 1e-6:
        raise PermissionDeniedException("The sum of section maximum_score must be 100")

    form = SurveyForm(title=data.title, company_id=company_id)
    session.add(form)
    await session.flush()  # para obtener form.id

    for section in data.sections:
        db_section = SurveySection(
            name=section.name,
            maximum_score=section.maximum_score,
            order=section.order,
            form_id=form.id,
        )
        session.add(db_section)
        await session.flush()

        for aspect in section.aspects:
            db_aspect = SurveyAspect(
                description=aspect.description,
                type=aspect.type,
                maximum_score=aspect.maximum_score,
                order=aspect.order,
                section_id=db_section.id,
            )
            session.add(db_aspect)

    # distribute linear weights and persist
    await _distribute_aspect_weights(session, form)

    await session.commit()
    await session.refresh(form)

    return form


async def update_survey_form(
    session: AsyncSession,
    form_id: int,
    company_id: int,
    data: SurveyFormsCreate,
) -> SurveyForm:
    # Verificar existencia
    result = await session.execute(
        select(SurveyForm).where(
            SurveyForm.id == form_id,
            SurveyForm.company_id == company_id,
            SurveyForm.deleted_at == None,
        )
    )
    form = result.scalar_one_or_none()
    if not form:
        raise NotFoundException("Form not found")

    # Validate sum of section maximums == 100
    total_sections = sum([sec.maximum_score for sec in data.sections])
    if abs(total_sections - 100.0) > 1e-6:
        raise PermissionDeniedException("The sum of section maximum_score must be 100")

    # Actualizar título
    form.title = data.title

    # Eliminar secciones y aspectos anteriores
    await session.execute(
        delete(SurveyAspect).where(
            SurveyAspect.section_id.in_(
                select(SurveySection.id).where(SurveySection.form_id == form_id)
            )
        )
    )
    await session.execute(delete(SurveySection).where(SurveySection.form_id == form_id))
    await session.flush()

    # Agregar nuevas secciones y aspectos
    for section in data.sections:
        db_section = SurveySection(
            name=section.name,
            maximum_score=section.maximum_score,
            order=section.order,
            form_id=form.id,
        )
        session.add(db_section)
        await session.flush()

        for aspect in section.aspects:
            db_aspect = SurveyAspect(
                description=aspect.description,
                type=aspect.type,
                maximum_score=aspect.maximum_score,
                order=aspect.order,
                section_id=db_section.id,
            )
            session.add(db_aspect)

    # recalculate aspect weights (lineal) and persist
    await _distribute_aspect_weights(session, form)

    await session.commit()
    await session.refresh(form)
    return form
async def get_form_by_id(session: AsyncSession, form_id: int, company_id: int) -> SurveyForm | None:
    result = await session.execute(
        select(SurveyForm).where(
            SurveyForm.id == form_id,
            SurveyForm.company_id == company_id,
            SurveyForm.deleted_at == None
        )
    )
    return result.scalar_one_or_none()

