from datetime import datetime
from typing import List, Optional
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
    SurveySectionCreate,
)
from app.types.pagination import Pagination
from app.utils.exeptions import NotFoundException


async def get_forms_by_company(
    session: AsyncSession,
    company_id: int,
    offset: int = 0,
    limit: int = Query(default=10, le=50),
    filter: Optional[str] = None,
    search: Optional[str] = None,
) -> SurveyFormsPublic:

    query = (
        select(SurveyForm, func.count().over().label("total"))
        .join(Company, SurveyForm.company_id == Company.id, isouter=True)
        .where(SurveyForm.company_id == company_id, SurveyForm.deleted_at == None)
        .order_by(SurveyForm.id)
        .offset(offset)
        .limit(limit)
    )

    if filter and search:
        match filter:
            case "title":
                query = query.where(SurveyForm.title.ilike(f"%{search}%"))

            case "company":
                query = query.where(Company.name.ilike(f"%{search}%"))

    result = await session.execute(query)
    db_forms = result.unique().all()

    if not db_forms:
        raise NotFoundException("Forms not found")

    forms = [row[0] for row in db_forms]
    total = db_forms[0][1] if db_forms else 0
    pagination = Pagination(first=offset, rows=limit, total=total)

    return SurveyFormsPublic(data=forms, pagination=pagination)


async def get_form_by_id(
    session: AsyncSession, form_id: int, company_id: int
) -> SurveyFormPublic:

    query = (
        select(SurveyForm)
        .options(selectinload(SurveyForm.sections).selectinload(SurveySection.aspects))
        .where(
            SurveyForm.id == form_id,
            SurveyForm.company_id == company_id,
            SurveyForm.deleted_at == None,
        )
    )

    result = await session.execute(query)
    db_forms = result.unique().scalar_one_or_none()

    if not db_forms:
        raise NotFoundException("Survey form not found")

    return db_forms


async def create_survey_form(
    session: AsyncSession, company_id: int, data: SurveyFormsCreate
) -> SurveyForm:

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
                maximum_score=aspect.maximum_score,
                order=aspect.order,
                section_id=db_section.id,
            )
            session.add(db_aspect)

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
                maximum_score=aspect.maximum_score,
                order=aspect.order,
                section_id=db_section.id,
            )
            session.add(db_aspect)

    await session.commit()
    await session.refresh(form)
    return form


async def soft_delete_form(
    session: AsyncSession, form_id: int, company_id: int
) -> SurveyForm:
    db_form = await get_form_by_id(session, form_id, company_id)
    db_form.deleted_at = datetime.now()

    await session.commit()
    await session.refresh(db_form)

    return SurveyForm.model_validate(db_form)
