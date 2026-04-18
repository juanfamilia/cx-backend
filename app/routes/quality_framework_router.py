"""API del Service Quality Framework (catálogo global + overrides por empresa).

Permisos:
  - role 0 (superadmin): CRUD completo del catálogo global y de templates.
  - role 1 (admin empresa): lectura del catálogo; CRUD de configs de su empresa.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_competency_config_model import (
    CompanyCompetencyConfig,
    CompanyCompetencyConfigCreate,
    CompanyCompetencyConfigPublic,
    CompanyCompetencyConfigUpdate,
)
from app.models.framework_model import (
    FrameworkCreate,
    FrameworkDimensionCreate,
    FrameworkDimensionPublic,
    FrameworkDimensionUpdate,
    FrameworkPublic,
    FrameworkUpdate,
)
from app.models.industry_model import (
    IndustriesPublic,
    IndustryCreate,
    IndustryPublic,
    IndustryUpdate,
)
from app.models.industry_template_model import (
    IndustryTemplateCreate,
    IndustryTemplatePublic,
    IndustryTemplateUpdate,
)
from app.models.quality_competency_model import (
    CompetencyFrameworkRefPublic,
    CompetencyIndicatorCreate,
    CompetencyIndicatorPublic,
    CompetencyIndicatorUpdate,
    IndicatorTypeEnum,
    QualityCompetencyCreate,
    QualityCompetencyPublic,
    QualityCompetenciesPublic,
    QualityCompetencyUpdate,
)
from app.services import quality_framework_services as qf
from app.types.quality_framework import (
    FrameworkListResponse,
    SuggestedSurveyAspectsResponse,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import NotFoundException, PermissionDeniedException

router = APIRouter(
    prefix="/quality",
    tags=["Quality Framework"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


def _require_superadmin(request: Request) -> None:
    if request.state.user.role != 0:
        raise PermissionDeniedException(
            custom_message="perform this action (superadmin only)"
        )


def _can_read_catalog(request: Request) -> None:
    if request.state.user.role not in (0, 1):
        raise PermissionDeniedException(custom_message="view the quality catalog")


def _require_company_access(request: Request, company_id: int) -> None:
    user = request.state.user
    if user.role == 0:
        return
    if user.role == 1 and user.company_id == company_id:
        return
    raise PermissionDeniedException(
        custom_message="access resources for this company"
    )


class FrameworkRefCreateBody(BaseModel):
    framework_dimension_id: int
    notes: Optional[str] = None


class IndicatorCreatePayload(BaseModel):
    """Cuerpo POST indicador (competency_id va en la URL)."""

    indicator_type: IndicatorTypeEnum = IndicatorTypeEnum.POSITIVE
    description: str
    detection_hint: Optional[str] = None
    order: int = 0


# ---------------------------------------------------------------------------
# Industries
# ---------------------------------------------------------------------------


@router.get("/industries", response_model=IndustriesPublic)
async def list_industries(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(50, le=200),
    search: Optional[str] = None,
    active_only: bool = True,
) -> IndustriesPublic:
    _can_read_catalog(request)
    return await qf.list_industries(session, offset, limit, search, active_only)


@router.get("/industries/{industry_id}", response_model=IndustryPublic)
async def get_industry(
    request: Request,
    industry_id: int,
    session: AsyncSession = Depends(get_db),
) -> IndustryPublic:
    _can_read_catalog(request)
    return await qf.get_industry(session, industry_id)


@router.post("/industries", response_model=IndustryPublic)
async def create_industry(
    request: Request,
    data: IndustryCreate,
    session: AsyncSession = Depends(get_db),
) -> IndustryPublic:
    _require_superadmin(request)
    return await qf.create_industry(session, data)


@router.put("/industries/{industry_id}", response_model=IndustryPublic)
async def update_industry(
    request: Request,
    industry_id: int,
    data: IndustryUpdate,
    session: AsyncSession = Depends(get_db),
) -> IndustryPublic:
    _require_superadmin(request)
    return await qf.update_industry(session, industry_id, data)


@router.delete("/industries/{industry_id}", status_code=204)
async def delete_industry(
    request: Request,
    industry_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_industry(session, industry_id)


# ---------------------------------------------------------------------------
# Frameworks
# ---------------------------------------------------------------------------


@router.get("/frameworks", response_model=FrameworkListResponse)
async def list_frameworks(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(50, le=200),
    search: Optional[str] = None,
) -> FrameworkListResponse:
    _can_read_catalog(request)
    data, pagination = await qf.list_frameworks(session, offset, limit, search)
    return FrameworkListResponse(data=data, pagination=pagination)


@router.get("/frameworks/{framework_id}", response_model=FrameworkPublic)
async def get_framework(
    request: Request,
    framework_id: int,
    session: AsyncSession = Depends(get_db),
) -> FrameworkPublic:
    _can_read_catalog(request)
    return await qf.get_framework(session, framework_id)


@router.post("/frameworks", response_model=FrameworkPublic)
async def create_framework(
    request: Request,
    data: FrameworkCreate,
    session: AsyncSession = Depends(get_db),
) -> FrameworkPublic:
    _require_superadmin(request)
    return await qf.create_framework(session, data)


@router.put("/frameworks/{framework_id}", response_model=FrameworkPublic)
async def update_framework(
    request: Request,
    framework_id: int,
    data: FrameworkUpdate,
    session: AsyncSession = Depends(get_db),
) -> FrameworkPublic:
    _require_superadmin(request)
    return await qf.update_framework(session, framework_id, data)


@router.delete("/frameworks/{framework_id}", status_code=204)
async def delete_framework(
    request: Request,
    framework_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_framework(session, framework_id)


# ---------------------------------------------------------------------------
# Framework dimensions
# ---------------------------------------------------------------------------


@router.post("/framework-dimensions", response_model=FrameworkDimensionPublic)
async def create_framework_dimension(
    request: Request,
    data: FrameworkDimensionCreate,
    session: AsyncSession = Depends(get_db),
) -> FrameworkDimensionPublic:
    _require_superadmin(request)
    return await qf.create_framework_dimension(session, data)


@router.put("/framework-dimensions/{dimension_id}", response_model=FrameworkDimensionPublic)
async def update_framework_dimension(
    request: Request,
    dimension_id: int,
    data: FrameworkDimensionUpdate,
    session: AsyncSession = Depends(get_db),
) -> FrameworkDimensionPublic:
    _require_superadmin(request)
    return await qf.update_framework_dimension(session, dimension_id, data)


@router.delete("/framework-dimensions/{dimension_id}", status_code=204)
async def delete_framework_dimension(
    request: Request,
    dimension_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_framework_dimension(session, dimension_id)


# ---------------------------------------------------------------------------
# Competencies
# ---------------------------------------------------------------------------


@router.get("/competencies", response_model=QualityCompetenciesPublic)
async def list_competencies(
    request: Request,
    session: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = Query(100, le=500),
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> QualityCompetenciesPublic:
    _can_read_catalog(request)
    return await qf.list_competencies(session, offset, limit, category, search)


@router.get("/competencies/{competency_id}", response_model=QualityCompetencyPublic)
async def get_competency(
    request: Request,
    competency_id: int,
    session: AsyncSession = Depends(get_db),
) -> QualityCompetencyPublic:
    _can_read_catalog(request)
    return await qf.get_competency(session, competency_id)


@router.post("/competencies", response_model=QualityCompetencyPublic)
async def create_competency(
    request: Request,
    data: QualityCompetencyCreate,
    session: AsyncSession = Depends(get_db),
) -> QualityCompetencyPublic:
    _require_superadmin(request)
    return await qf.create_competency(session, data)


@router.put("/competencies/{competency_id}", response_model=QualityCompetencyPublic)
async def update_competency(
    request: Request,
    competency_id: int,
    data: QualityCompetencyUpdate,
    session: AsyncSession = Depends(get_db),
) -> QualityCompetencyPublic:
    _require_superadmin(request)
    return await qf.update_competency(session, competency_id, data)


@router.delete("/competencies/{competency_id}", status_code=204)
async def delete_competency(
    request: Request,
    competency_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_competency(session, competency_id)


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


@router.post(
    "/competencies/{competency_id}/indicators",
    response_model=CompetencyIndicatorPublic,
)
async def create_indicator(
    request: Request,
    competency_id: int,
    data: IndicatorCreatePayload,
    session: AsyncSession = Depends(get_db),
) -> CompetencyIndicatorPublic:
    _require_superadmin(request)
    payload = CompetencyIndicatorCreate(
        competency_id=competency_id,
        **data.model_dump(),
    )
    return await qf.create_indicator(session, payload)


@router.put("/indicators/{indicator_id}", response_model=CompetencyIndicatorPublic)
async def update_indicator(
    request: Request,
    indicator_id: int,
    data: CompetencyIndicatorUpdate,
    session: AsyncSession = Depends(get_db),
) -> CompetencyIndicatorPublic:
    _require_superadmin(request)
    return await qf.update_indicator(session, indicator_id, data)


@router.delete("/indicators/{indicator_id}", status_code=204)
async def delete_indicator(
    request: Request,
    indicator_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_indicator(session, indicator_id)


# ---------------------------------------------------------------------------
# Competency ↔ framework dimension
# ---------------------------------------------------------------------------


@router.post(
    "/competencies/{competency_id}/framework-refs",
    response_model=CompetencyFrameworkRefPublic,
)
async def create_framework_ref(
    request: Request,
    competency_id: int,
    body: FrameworkRefCreateBody,
    session: AsyncSession = Depends(get_db),
) -> CompetencyFrameworkRefPublic:
    _require_superadmin(request)
    return await qf.create_competency_framework_ref(
        session,
        competency_id,
        body.framework_dimension_id,
        body.notes,
    )


@router.delete("/framework-refs/{ref_id}", status_code=204)
async def delete_framework_ref(
    request: Request,
    ref_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.delete_competency_framework_ref(session, ref_id)


# ---------------------------------------------------------------------------
# Industry templates
# ---------------------------------------------------------------------------


@router.get(
    "/industries/{industry_id}/template",
    response_model=List[IndustryTemplatePublic],
)
async def list_industry_template(
    request: Request,
    industry_id: int,
    session: AsyncSession = Depends(get_db),
) -> List[IndustryTemplatePublic]:
    _can_read_catalog(request)
    return await qf.list_industry_template(session, industry_id)


@router.post("/industry-templates", response_model=IndustryTemplatePublic)
async def upsert_industry_template(
    request: Request,
    data: IndustryTemplateCreate,
    session: AsyncSession = Depends(get_db),
) -> IndustryTemplatePublic:
    _require_superadmin(request)
    return await qf.upsert_industry_template(session, data)


@router.put("/industry-templates/{template_id}", response_model=IndustryTemplatePublic)
async def update_industry_template(
    request: Request,
    template_id: int,
    data: IndustryTemplateUpdate,
    session: AsyncSession = Depends(get_db),
) -> IndustryTemplatePublic:
    _require_superadmin(request)
    return await qf.update_industry_template(session, template_id, data)


@router.delete("/industry-templates/{template_id}", status_code=204)
async def delete_industry_template(
    request: Request,
    template_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    _require_superadmin(request)
    await qf.soft_delete_industry_template(session, template_id)


# ---------------------------------------------------------------------------
# Company competency configs
# ---------------------------------------------------------------------------


@router.get(
    "/companies/{company_id}/competency-configs",
    response_model=List[CompanyCompetencyConfigPublic],
)
async def list_company_competency_configs(
    request: Request,
    company_id: int,
    session: AsyncSession = Depends(get_db),
) -> List[CompanyCompetencyConfigPublic]:
    _require_company_access(request, company_id)
    return await qf.list_company_competency_configs(session, company_id)


@router.post(
    "/companies/{company_id}/competency-configs",
    response_model=CompanyCompetencyConfigPublic,
)
async def upsert_company_competency_config(
    request: Request,
    company_id: int,
    data: CompanyCompetencyConfigCreate,
    session: AsyncSession = Depends(get_db),
) -> CompanyCompetencyConfigPublic:
    _require_company_access(request, company_id)
    uid = request.state.user.id
    payload = CompanyCompetencyConfigCreate(
        company_id=company_id,
        competency_id=data.competency_id,
        is_enabled=data.is_enabled,
        custom_weight=data.custom_weight,
        custom_notes=data.custom_notes,
        created_by_user_id=uid if request.state.user.role == 1 else data.created_by_user_id,
    )
    return await qf.upsert_company_competency_config(session, company_id, payload)


@router.put(
    "/competency-configs/{config_id}",
    response_model=CompanyCompetencyConfigPublic,
)
async def update_company_competency_config(
    request: Request,
    config_id: int,
    data: CompanyCompetencyConfigUpdate,
    session: AsyncSession = Depends(get_db),
) -> CompanyCompetencyConfigPublic:
    row = await session.get(CompanyCompetencyConfig, config_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Config not found")
    _require_company_access(request, row.company_id)
    return await qf.update_company_competency_config(session, config_id, data)


@router.delete("/competency-configs/{config_id}", status_code=204)
async def delete_company_competency_config(
    request: Request,
    config_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    row = await session.get(CompanyCompetencyConfig, config_id)
    if not row or row.deleted_at is not None:
        raise NotFoundException("Config not found")
    _require_company_access(request, row.company_id)
    await qf.soft_delete_company_competency_config(session, config_id)


# ---------------------------------------------------------------------------
# Suggested survey aspects (form builder)
# ---------------------------------------------------------------------------


@router.get(
    "/companies/{company_id}/suggested-survey-aspects",
    response_model=SuggestedSurveyAspectsResponse,
)
async def suggested_survey_aspects(
    request: Request,
    company_id: int,
    session: AsyncSession = Depends(get_db),
) -> SuggestedSurveyAspectsResponse:
    _require_company_access(request, company_id)
    return await qf.get_suggested_survey_aspects(session, company_id)
