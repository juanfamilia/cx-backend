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

from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(session):
    try:
        yield
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e

async def _distribute_aspect_weights(session: AsyncSession, form: SurveyForm):
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

async def _validate_and_distribute_section_aspects(section, reflexive_exceptions=True):
    # Suponiendo types: 'NUMBER' para score, 'BOOLEAN' para yes/no
    number_sum = sum(aspect.maximum_score for aspect in section.aspects if aspect.type == "NUMBER")
    boolean_count = sum(1 for aspect in section.aspects if aspect.type == "BOOLEAN")
    restante = section.maximum_score - number_sum
    
    if restante < 0:
        raise PermissionDeniedException(
            f"La suma de los aspectos de tipo Número ({number_sum}) excede el máximo de la sección '{section.name}' ({section.maximum_score}). Revisa los valores."
        )
    
    # Asignación automática
    if boolean_count > 0:
        boolean_value = restante / boolean_count
        for aspect in section.aspects:
            if aspect.type == "BOOLEAN":
                aspect.maximum_score = boolean_value

    total_aspects = sum(aspect.maximum_score for aspect in section.aspects)
    
    if abs(total_aspects - section.maximum_score) > 1e-6 and reflexive_exceptions:
        raise PermissionDeniedException(
            f"La suma de los puntos asignados a los aspectos de la sección '{section.name}' ({total_aspects}) no coincide con el máximo ({section.maximum_score}). ¿Deseas que el sistema distribuya automáticamente el puntaje restante entre los aspectos tipo Sí/No, o prefieres corregir manualmente los valores?"
        )

async def create_survey_form(
    session: AsyncSession, company_id: int, data: SurveyFormsCreate
) -> SurveyForm:
    total_sections = sum(sec.maximum_score for sec in data.sections)
    if abs(total_sections - 100.0) > 1e-6:
        raise PermissionDeniedException("The sum of section maximum_score must be 100")

    # Validar y distribuir aspectos por sección
    for section in data.sections:
        await _validate_and_distribute_section_aspects(section)

    async with transaction(session):
        form = SurveyForm(title=data.title, company_id=company_id)
        session.add(form)
        await session.flush()

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

        await _distribute_aspect_weights(session, form)
        await session.refresh(form)
        return form

async def update_survey_form(
    session: AsyncSession,
    form_id: int,
    company_id: int,
    data: SurveyFormsCreate,
) -> SurveyForm:
    total_sections = sum(sec.maximum_score for sec in data.sections)
    if abs(total_sections - 100.0) > 1e-6:
        raise PermissionDeniedException("The sum of section maximum_score must be 100")

    for section in data.sections:
        await _validate_and_distribute_section_aspects(section)

    async with transaction(session):
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

        form.title = data.title

        await session.execute(
            delete(SurveyAspect).where(
                SurveyAspect.section_id.in_(
                    select(SurveySection.id).where(SurveySection.form_id == form_id)
                )
            )
        )
        await session.execute(delete(SurveySection).where(SurveySection.form_id == form_id))
        await session.flush()

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

        await _distribute_aspect_weights(session, form)
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

async def get_forms_by_company(
    session: AsyncSession,
    company_id: int,
    offset: int = 0,
    limit: int = 10,
    filter: Optional[str] = None,
    search: Optional[str] = None
) -> SurveyFormsPublic:
    query = select(SurveyForm).where(
        SurveyForm.company_id == company_id,
        SurveyForm.deleted_at == None
    )
    if filter:
        query = query.where(SurveyForm.status == filter)
    if search:
        search_term = f"%{search}%"
        query = query.where(SurveyForm.title.ilike(search_term))
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    forms = result.scalars().all()
    return SurveyFormsPublic(items=forms, total=len(forms))

async def soft_delete_form(session: AsyncSession, form_id: int):
    result = await session.execute(
        select(SurveyForm).where(SurveyForm.id == form_id, SurveyForm.deleted_at == None)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise NotFoundException("Form not found")
    form.deleted_at = datetime.utcnow()
    session.add(form)
    await session.commit()
    return form
