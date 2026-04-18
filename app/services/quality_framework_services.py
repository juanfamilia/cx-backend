"""Servicios del Service Quality Framework (catálogo global + overrides por empresa)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.company_competency_config_model import (
    CompanyCompetencyConfig,
    CompanyCompetencyConfigCreate,
    CompanyCompetencyConfigPublic,
    CompanyCompetencyConfigUpdate,
)
from app.models.company_model import Company
from app.models.framework_model import (
    Framework,
    FrameworkCreate,
    FrameworkDimension,
    FrameworkDimensionCreate,
    FrameworkDimensionPublic,
    FrameworkDimensionUpdate,
    FrameworkPublic,
    FrameworkUpdate,
)
from app.models.industry_model import (
    Industry,
    IndustryCreate,
    IndustryPublic,
    IndustryUpdate,
    IndustriesPublic,
)
from app.models.industry_template_model import (
    IndustryTemplate,
    IndustryTemplateCreate,
    IndustryTemplatePublic,
    IndustryTemplateUpdate,
)
from app.models.quality_competency_model import (
    CompetencyFrameworkRef,
    CompetencyFrameworkRefPublic,
    CompetencyIndicator,
    CompetencyIndicatorCreate,
    CompetencyIndicatorPublic,
    CompetencyIndicatorUpdate,
    QualityCompetency,
    QualityCompetencyCreate,
    QualityCompetencyPublic,
    QualityCompetenciesPublic,
)
from app.types.pagination import Pagination
from app.types.quality_framework import (
    SuggestedSurveyAspectItem,
    SuggestedSurveyAspectsResponse,
)
from app.utils.exeptions import NotFoundException


def _measurement_to_aspect_type(mt: str) -> str:
    """Mapea measurement_type de competencia → aspect type del formulario."""
    mapping = {
        "boolean": "boolean",
        "likert": "likert",
        "number": "number",
    }
    return mapping.get(mt.lower(), "likert")


# ---------------------------------------------------------------------------
# Industries
# ---------------------------------------------------------------------------


async def list_industries(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    active_only: bool = True,
) -> IndustriesPublic:
    q = select(Industry, func.count().over().label("total")).where(
        Industry.deleted_at.is_(None)
    )
    if active_only:
        q = q.where(Industry.is_active.is_(True))
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Industry.name.ilike(term),
                Industry.code.ilike(term),
            )
        )
    q = q.order_by(Industry.code).offset(offset).limit(limit)
    rows = (await session.execute(q)).unique().all()
    if not rows:
        return IndustriesPublic(
            data=[],
            pagination=Pagination(first=offset, rows=limit, total=0),
        )
    items = [IndustryPublic.model_validate(r[0]) for r in rows]
    total = int(rows[0][1]) if rows else 0
    return IndustriesPublic(
        data=items,
        pagination=Pagination(first=offset, rows=limit, total=total),
    )


async def get_industry(session: AsyncSession, industry_id: int) -> IndustryPublic:
    row = await session.get(Industry, industry_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Industry not found")
    return IndustryPublic.model_validate(row)


async def create_industry(
    session: AsyncSession, data: IndustryCreate
) -> IndustryPublic:
    obj = Industry(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return IndustryPublic.model_validate(obj)


async def update_industry(
    session: AsyncSession, industry_id: int, data: IndustryUpdate
) -> IndustryPublic:
    row = await session.get(Industry, industry_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Industry not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return IndustryPublic.model_validate(row)


async def soft_delete_industry(session: AsyncSession, industry_id: int) -> None:
    row = await session.get(Industry, industry_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Industry not found")
    row.deleted_at = datetime.now()
    row.is_active = False
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Frameworks
# ---------------------------------------------------------------------------


async def list_frameworks(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[FrameworkPublic], Pagination]:
    q = select(Framework, func.count().over().label("total")).where(
        Framework.deleted_at.is_(None)
    )
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Framework.name.ilike(term),
                Framework.code.ilike(term),
            )
        )
    q = q.order_by(Framework.code).offset(offset).limit(limit)
    rows = (await session.execute(q)).unique().all()
    if not rows:
        return [], Pagination(first=offset, rows=limit, total=0)
    total = int(rows[0][1])
    out = []
    for r, _ in rows:
        dims = (
            await session.execute(
                select(FrameworkDimension)
                .where(
                    FrameworkDimension.framework_id == r.id,
                    FrameworkDimension.deleted_at.is_(None),
                )
                .order_by(FrameworkDimension.order, FrameworkDimension.code)
            )
        ).scalars().all()
        fp = FrameworkPublic.model_validate(r)
        fp.dimensions = [FrameworkDimensionPublic.model_validate(d) for d in dims]
        out.append(fp)
    return out, Pagination(first=offset, rows=limit, total=total)


async def get_framework(session: AsyncSession, framework_id: int) -> FrameworkPublic:
    r = await session.get(Framework, framework_id)
    if not r or r.deleted_at is not None:
        raise NotFoundException("Framework not found")
    dims = (
        await session.execute(
            select(FrameworkDimension)
            .where(
                FrameworkDimension.framework_id == r.id,
                FrameworkDimension.deleted_at.is_(None),
            )
            .order_by(FrameworkDimension.order, FrameworkDimension.code)
        )
    ).scalars().all()
    fp = FrameworkPublic.model_validate(r)
    fp.dimensions = [FrameworkDimensionPublic.model_validate(d) for d in dims]
    return fp


async def create_framework(
    session: AsyncSession, data: FrameworkCreate
) -> FrameworkPublic:
    obj = Framework(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return FrameworkPublic.model_validate(obj)


async def update_framework(
    session: AsyncSession, framework_id: int, data: FrameworkUpdate
) -> FrameworkPublic:
    row = await session.get(Framework, framework_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Framework not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FrameworkPublic.model_validate(row)


async def soft_delete_framework(session: AsyncSession, framework_id: int) -> None:
    row = await session.get(Framework, framework_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Framework not found")
    row.deleted_at = datetime.now()
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Framework dimensions
# ---------------------------------------------------------------------------


async def create_framework_dimension(
    session: AsyncSession, data: FrameworkDimensionCreate
) -> FrameworkDimensionPublic:
    obj = FrameworkDimension(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return FrameworkDimensionPublic.model_validate(obj)


async def update_framework_dimension(
    session: AsyncSession, dimension_id: int, data: FrameworkDimensionUpdate
) -> FrameworkDimensionPublic:
    row = await session.get(FrameworkDimension, dimension_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Framework dimension not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return FrameworkDimensionPublic.model_validate(row)


async def soft_delete_framework_dimension(
    session: AsyncSession, dimension_id: int
) -> None:
    row = await session.get(FrameworkDimension, dimension_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Framework dimension not found")
    row.deleted_at = datetime.now()
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Competencies
# ---------------------------------------------------------------------------


async def list_competencies(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> QualityCompetenciesPublic:
    q = select(QualityCompetency, func.count().over().label("total")).where(
        QualityCompetency.deleted_at.is_(None)
    )
    if category:
        q = q.where(QualityCompetency.category == category)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                QualityCompetency.name.ilike(term),
                QualityCompetency.code.ilike(term),
            )
        )
    q = q.order_by(QualityCompetency.category, QualityCompetency.code).offset(
        offset
    ).limit(limit)
    rows = (await session.execute(q)).unique().all()
    if not rows:
        return QualityCompetenciesPublic(
            data=[],
            pagination=Pagination(first=offset, rows=limit, total=0),
        )
    total = int(rows[0][1])
    data: List[QualityCompetencyPublic] = []
    for r, _ in rows:
        data.append(await _competency_to_public(session, r))
    return QualityCompetenciesPublic(
        data=data,
        pagination=Pagination(first=offset, rows=limit, total=total),
    )


async def _competency_to_public(
    session: AsyncSession, r: QualityCompetency
) -> QualityCompetencyPublic:
    inds = (
        await session.execute(
            select(CompetencyIndicator)
            .where(
                CompetencyIndicator.competency_id == r.id,
                CompetencyIndicator.deleted_at.is_(None),
            )
            .order_by(CompetencyIndicator.order, CompetencyIndicator.id)
        )
    ).scalars().all()
    refs_rows = (
        await session.execute(
            select(CompetencyFrameworkRef, FrameworkDimension)
            .join(FrameworkDimension)
            .where(
                CompetencyFrameworkRef.competency_id == r.id,
                FrameworkDimension.deleted_at.is_(None),
            )
        )
    ).all()
    pub = QualityCompetencyPublic.model_validate(r)
    pub.indicators = [CompetencyIndicatorPublic.model_validate(i) for i in inds]
    pub.framework_refs = []
    for ref, dim in refs_rows:
        rp = CompetencyFrameworkRefPublic.model_validate(ref)
        rp.dimension = FrameworkDimensionPublic.model_validate(dim)
        pub.framework_refs.append(rp)
    return pub


async def get_competency(
    session: AsyncSession, competency_id: int
) -> QualityCompetencyPublic:
    r = await session.get(QualityCompetency, competency_id)
    if not r or r.deleted_at is not None:
        raise NotFoundException("Competency not found")
    return await _competency_to_public(session, r)


async def create_competency(
    session: AsyncSession, data: QualityCompetencyCreate
) -> QualityCompetencyPublic:
    obj = QualityCompetency(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return await get_competency(session, obj.id)


async def update_competency(
    session: AsyncSession, competency_id: int, data: QualityCompetencyUpdate
) -> QualityCompetencyPublic:
    row = await session.get(QualityCompetency, competency_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Competency not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return await get_competency(session, row.id)


async def soft_delete_competency(session: AsyncSession, competency_id: int) -> None:
    row = await session.get(QualityCompetency, competency_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Competency not found")
    row.deleted_at = datetime.now()
    row.is_active = False
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


async def create_indicator(
    session: AsyncSession, data: CompetencyIndicatorCreate
) -> CompetencyIndicatorPublic:
    obj = CompetencyIndicator(**data.model_dump())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return CompetencyIndicatorPublic.model_validate(obj)


async def update_indicator(
    session: AsyncSession, indicator_id: int, data: CompetencyIndicatorUpdate
) -> CompetencyIndicatorPublic:
    row = await session.get(CompetencyIndicator, indicator_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Indicator not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return CompetencyIndicatorPublic.model_validate(row)


async def soft_delete_indicator(session: AsyncSession, indicator_id: int) -> None:
    row = await session.get(CompetencyIndicator, indicator_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Indicator not found")
    row.deleted_at = datetime.now()
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Competency ↔ framework dimension refs
# ---------------------------------------------------------------------------


async def create_competency_framework_ref(
    session: AsyncSession,
    competency_id: int,
    framework_dimension_id: int,
    notes: Optional[str] = None,
) -> CompetencyFrameworkRefPublic:
    ref = CompetencyFrameworkRef(
        competency_id=competency_id,
        framework_dimension_id=framework_dimension_id,
        notes=notes,
    )
    session.add(ref)
    await session.commit()
    await session.refresh(ref)
    dim = await session.get(FrameworkDimension, framework_dimension_id)
    rp = CompetencyFrameworkRefPublic.model_validate(ref)
    if dim:
        rp.dimension = FrameworkDimensionPublic.model_validate(dim)
    return rp


async def delete_competency_framework_ref(
    session: AsyncSession, ref_id: int
) -> None:
    row = await session.get(CompetencyFrameworkRef, ref_id)
    if not row:
        raise NotFoundException("Reference not found")
    await session.execute(
        delete(CompetencyFrameworkRef).where(CompetencyFrameworkRef.id == ref_id)
    )
    await session.commit()


# ---------------------------------------------------------------------------
# Industry templates
# ---------------------------------------------------------------------------


async def list_industry_template(
    session: AsyncSession, industry_id: int
) -> List[IndustryTemplatePublic]:
    await get_industry(session, industry_id)  # 404 if missing
    q = (
        select(IndustryTemplate)
        .where(
            IndustryTemplate.industry_id == industry_id,
            IndustryTemplate.deleted_at.is_(None),
        )
        .options(selectinload(IndustryTemplate.competency))  # type: ignore[arg-type]
    )
    rows = (await session.execute(q)).scalars().all()
    out: List[IndustryTemplatePublic] = []
    for r in rows:
        ip = IndustryTemplatePublic.model_validate(r)
        if r.competency:
            ip.competency = await _competency_to_public(session, r.competency)
        out.append(ip)
    return sorted(out, key=lambda x: (x.competency.code if x.competency else "", x.id))


async def upsert_industry_template(
    session: AsyncSession, data: IndustryTemplateCreate
) -> IndustryTemplatePublic:
    await get_industry(session, data.industry_id)
    await get_competency(session, data.competency_id)
    existing = (
        await session.execute(
            select(IndustryTemplate).where(
                IndustryTemplate.industry_id == data.industry_id,
                IndustryTemplate.competency_id == data.competency_id,
                IndustryTemplate.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.suggested_weight = data.suggested_weight
        existing.is_mandatory = data.is_mandatory
        existing.notes = data.notes
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        it = existing
    else:
        it = IndustryTemplate(**data.model_dump())
        session.add(it)
        await session.commit()
        await session.refresh(it)
    ip = IndustryTemplatePublic.model_validate(it)
    ip.competency = await get_competency(session, it.competency_id)
    return ip


async def update_industry_template(
    session: AsyncSession, template_id: int, data: IndustryTemplateUpdate
) -> IndustryTemplatePublic:
    row = await session.get(IndustryTemplate, template_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Industry template not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    ip = IndustryTemplatePublic.model_validate(row)
    ip.competency = await get_competency(session, row.competency_id)
    return ip


async def soft_delete_industry_template(
    session: AsyncSession, template_id: int
) -> None:
    row = await session.get(IndustryTemplate, template_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Industry template not found")
    row.deleted_at = datetime.now()
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Company competency configs
# ---------------------------------------------------------------------------


async def list_company_competency_configs(
    session: AsyncSession, company_id: int
) -> List[CompanyCompetencyConfigPublic]:
    company = await session.get(Company, company_id)
    if not company or company.deleted_at is not None:
        raise NotFoundException("Company not found")
    q = (
        select(CompanyCompetencyConfig)
        .where(
            CompanyCompetencyConfig.company_id == company_id,
            CompanyCompetencyConfig.deleted_at.is_(None),
        )
        .options(selectinload(CompanyCompetencyConfig.competency))  # type: ignore[arg-type]
    )
    rows = (await session.execute(q)).scalars().all()
    out: List[CompanyCompetencyConfigPublic] = []
    for r in rows:
        cp = CompanyCompetencyConfigPublic.model_validate(r)
        if r.competency:
            cp.competency = await _competency_to_public(session, r.competency)
        out.append(cp)
    return out


async def upsert_company_competency_config(
    session: AsyncSession,
    company_id: int,
    data: CompanyCompetencyConfigCreate,
) -> CompanyCompetencyConfigPublic:
    if data.company_id != company_id:
        data = CompanyCompetencyConfigCreate(
            company_id=company_id,
            competency_id=data.competency_id,
            is_enabled=data.is_enabled,
            custom_weight=data.custom_weight,
            custom_notes=data.custom_notes,
            created_by_user_id=data.created_by_user_id,
        )
    company = await session.get(Company, company_id)
    if not company or company.deleted_at is not None:
        raise NotFoundException("Company not found")
    await get_competency(session, data.competency_id)
    existing = (
        await session.execute(
            select(CompanyCompetencyConfig).where(
                CompanyCompetencyConfig.company_id == company_id,
                CompanyCompetencyConfig.competency_id == data.competency_id,
                CompanyCompetencyConfig.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.is_enabled = data.is_enabled
        existing.custom_weight = data.custom_weight
        existing.custom_notes = data.custom_notes
        if data.created_by_user_id is not None:
            existing.created_by_user_id = data.created_by_user_id
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        row = existing
    else:
        row = CompanyCompetencyConfig(**data.model_dump())
        session.add(row)
        await session.commit()
        await session.refresh(row)
    cp = CompanyCompetencyConfigPublic.model_validate(row)
    cp.competency = await get_competency(session, row.competency_id)
    return cp


async def update_company_competency_config(
    session: AsyncSession,
    config_id: int,
    data: CompanyCompetencyConfigUpdate,
) -> CompanyCompetencyConfigPublic:
    row = await session.get(CompanyCompetencyConfig, config_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Config not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    cp = CompanyCompetencyConfigPublic.model_validate(row)
    cp.competency = await get_competency(session, row.competency_id)
    return cp


async def soft_delete_company_competency_config(
    session: AsyncSession, config_id: int
) -> None:
    row = await session.get(CompanyCompetencyConfig, config_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Config not found")
    row.deleted_at = datetime.now()
    session.add(row)
    await session.commit()


# ---------------------------------------------------------------------------
# Suggested survey aspects (para constructor de formularios)
# ---------------------------------------------------------------------------


async def get_suggested_survey_aspects(
    session: AsyncSession, company_id: int
) -> SuggestedSurveyAspectsResponse:
    company = await session.get(Company, company_id)
    if not company or company.deleted_at is not None:
        raise NotFoundException("Company not found")
    industry_id = company.industry_id
    if industry_id is None:
        return SuggestedSurveyAspectsResponse(
            company_id=company_id,
            industry_id=None,
            items=[],
        )

    templates = await list_industry_template(session, industry_id)
    configs = {
        c.competency_id: c
        for c in await list_company_competency_configs(session, company_id)
    }

    items: List[SuggestedSurveyAspectItem] = []
    for order, tpl in enumerate(templates):
        comp = tpl.competency
        if not comp:
            continue
        cfg = configs.get(comp.id)
        if cfg and cfg.is_enabled is False:
            continue
        weight = float(
            cfg.custom_weight
            if cfg and cfg.custom_weight is not None
            else tpl.suggested_weight
        )
        desc = comp.definition or comp.name
        if cfg and cfg.custom_notes:
            desc = f"{desc}\n\n(Notas empresa: {cfg.custom_notes})"
        mt_raw = comp.measurement_type
        mt = mt_raw.value if hasattr(mt_raw, "value") else str(mt_raw)
        items.append(
            SuggestedSurveyAspectItem(
                competency_id=comp.id,
                competency_code=comp.code,
                name=comp.name,
                suggested_description=desc,
                suggested_type=_measurement_to_aspect_type(mt),
                suggested_order=order,
                weight_hint=weight,
                is_mandatory=bool(tpl.is_mandatory),
            )
        )
    return SuggestedSurveyAspectsResponse(
        company_id=company_id,
        industry_id=industry_id,
        items=items,
    )
