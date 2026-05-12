"""
Siete Field — proyectos de control de levantamiento (MVP interno, CSV-ready).

Prefijo: `/api/v1/field`
"""

from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import Company
from app.models.field_ledger_model import (
    FieldFindingDecisionLogPublic,
    FieldFindingPublic,
    FieldImportRowPublic,
    FieldLedgerEventPublic,
)
from app.models.field_decision_model import (
    DoobloAnalysisRequest,
    FieldFindingApprovalBody,
    FieldOperationalSnapshotPublic,
    FieldPolicySetCreate,
    FieldPolicySetPublic,
    FieldProjectExternalSourceCreate,
    FieldProjectExternalSourcePublic,
    FieldSyncRunPublic,
)
from app.models.field_project_model import (
    FieldImportRunPublic,
    FieldProjectCreate,
    FieldProjectPatch,
    FieldProjectPublic,
)
from app.models.field_execution_model import (
    FieldMetricPublic,
    FieldProjectSyncResponse,
    FieldSurveyPublic,
)
from app.models.field_overview_model import FieldProjectOverviewRow
from app.models.field_instrument_qa_run_model import (
    FieldInstrumentQARunPublic,
    InstrumentQAExecuteResponse,
)
from app.models.field_instrument_revision_model import (
    FieldInstrumentRevisionCreate,
    FieldInstrumentRevisionPatch,
    FieldInstrumentRevisionPublic,
    FieldInstrumentRevisionValidateResponse,
    FieldInstrumentRevisionWithSpec,
    InstrumentSpecValidateBody,
    InstrumentSpecValidationReport,
)
from app.models.field_framework_template_model import FieldFrameworkTemplatePublic
from app.models.field_framework_waiver_model import (
    FieldFrameworkWaiverCreate,
    FieldFrameworkWaiverPublic,
)
from app.models.field_study_brief_model import FieldStudyBriefPatch, FieldStudyBriefPublic
from app.models.field_study_model import FieldStudyCreate, FieldStudyPublic
from app.models.field_readiness_model import (
    FieldReadinessPolicyPublic,
    FieldReadinessPolicyUpsert,
    FieldReadinessSignatoryCreate,
    FieldReadinessSignatoryPublic,
    ReadinessGatePublic,
    ReadinessSignBody,
    ReadinessSignResult,
)
from app.services.field_decision_services import (
    create_external_source,
    create_policy_set,
    create_sync_run_for_dooblo_analysis,
    get_operational_snapshot,
    list_external_sources,
    list_policy_sets,
    list_finding_decision_log,
    list_project_findings,
    list_sync_runs,
    set_finding_approval,
)
from app.services.field_dooblo_analysis_task import run_dooblo_analysis_task
from app.services.field_import_services import import_field_csv_2026_1
from app.services.field_ledger_services import (
    list_findings_for_run,
    list_import_runs_for_project,
    list_ledger_events_for_project,
    list_rows_for_run,
)
from app.services.field_framework_template_services import (
    FRAMEWORK_TEMPLATE_STUDY_TYPES,
    list_field_framework_templates_for_api,
)
from app.services.field_execution_services import (
    list_project_kpis,
    list_project_surveys,
    sync_field_project_from_sources,
)
from app.services.field_overview_services import (
    get_field_project_overview_drilldown,
    list_field_projects_overview,
)
from app.services.field_project_services import (
    create_field_project,
    list_field_projects,
    patch_field_project,
)
from app.services.field_dooblo_catalog_service import (
    list_dooblo_customer_projects_catalog,
    list_dooblo_customers_catalog,
    list_dooblo_organization_studio_projects_catalog,
    list_dooblo_project_surveys_catalog,
)
from app.services.field_instrument_qa_services import (
    execute_instrument_qa_bootstrap_run,
    list_instrument_qa_runs,
)
from app.services.field_instrument_revision_services import (
    create_instrument_revision,
    get_instrument_revision,
    list_instrument_revisions_for_study,
    patch_instrument_revision,
    validate_instrument_revision_and_persist,
    validate_instrument_spec_inline,
)
from app.services.field_readiness_services import (
    create_readiness_signatory,
    get_readiness_for_revision,
    get_readiness_policy_for_reader,
    list_readiness_signatories,
    sign_readiness_for_revision,
    soft_delete_readiness_signatory,
    upsert_company_readiness_policy,
)
from app.services.field_framework_waiver_services import (
    create_framework_waiver_for_revision,
    list_framework_waivers_for_revision,
)
from app.services.field_study_brief_services import (
    approve_field_study_brief_client,
    approve_field_study_brief_internal,
    get_field_study_brief_public,
    patch_field_study_brief,
)
from app.services.field_study_services import create_field_study, list_field_studies
from app.services.company_dooblo_service import (
    get_dooblo_creds_for_company,
    get_dooblo_settings_public,
    upsert_dooblo_settings,
)
from app.services.company_qualtrics_service import (
    get_qualtrics_settings_public,
    upsert_qualtrics_settings,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.field_access import require_field_product_access
from app.models.company_dooblo_model import CompanyDoobloPutBody
from app.models.company_qualtrics_model import CompanyQualtricsPutBody
from app.models.dooblo_catalog_model import OrganizationStudioProjectsCatalogPage, RemoteFieldCatalogPage
from app.integrations import dooblo_client as dooblo
from app.integrations.dooblo_serialize import httpx_response_to_proxy_dict

router = APIRouter(
    prefix="/field",
    tags=["Siete Field"],
    dependencies=[
        Depends(get_auth_user),
        Depends(check_company_payment_status),
    ],
)

# Llamadas Dooblo adicionales (misma newapi) sin wrapper dedicado: lista blanca.
DOOBLO_RAW_ALLOWED = frozenset(
    {
        "ProjectSurveys",
        "Surveys",
        "SimpleSurveyExport",
        "SurveyInterviewIDs",
        "SurveyInterviewIDsByLastModified",
        "SurveyInterviewData",
        "SimpleExport",
        "OperationData",
        "GetSurveyQuotasStatus",
        "QuotaStructure",
        "HandlingExamples",
        "GetSurveyorsRoute",
        "Customers",
        "CustomerProjects",
    }
)


def _dooblo_proxy(r: httpx.Response) -> dict:
    return httpx_response_to_proxy_dict(r)


def _resolve_effective_company_id_for_field(
    request: Request, company_id: int | None
) -> int:
    u = request.state.user
    if u.role == 0:
        if company_id is None or company_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Indique company_id (ID de la empresa cuyo Dooblo desea administrar o consultar).",
            )
        return int(company_id)
    if u.company_id is None:
        raise HTTPException(
            status_code=403, detail="Usuario sin empresa: no se puede vincular Dooblo."
        )
    if company_id is not None and int(company_id) != int(u.company_id):
        raise HTTPException(
            status_code=403, detail="Solo puede operar con Dooblo de su propia empresa."
        )
    return int(u.company_id)


async def _dooblo_creds_for_request_or_503(
    session: AsyncSession, request: Request, company_id: int | None
) -> dooblo.DoobloCreds:
    cid = _resolve_effective_company_id_for_field(request, company_id)
    c = await get_dooblo_creds_for_company(session, cid)
    if c is None:
        raise HTTPException(
            status_code=503,
            detail="Dooblo no está configurado para esta empresa. Guárdelos en Siete Field o use variables DOOBLO_* en el servidor.",
        )
    return c


@router.get(
    "/dooblo/status",
    dependencies=[Depends(require_field_product_access)],
    summary="Estado de credenciales Dooblo para la empresa (sin exponer claves).",
)
async def field_dooblo_status(
    request: Request,
    company_id: int | None = Query(
        None, description="Superadmin: empresa objetivo. Otros roles usan su propia company."
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    out = await get_dooblo_settings_public(session, request.state.user, cid)
    out["dooblo_configured"] = out.get("configured", False)
    return out


@router.get(
    "/dooblo/credentials",
    dependencies=[Depends(require_field_product_access)],
    summary="Ver configuración Dooblo por empresa (sin contraseña).",
)
async def field_dooblo_get_credentials(
    request: Request,
    company_id: int | None = Query(
        None, description="Superadmin: ID de la empresa. Obligatorio para rol 0."
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    return await get_dooblo_settings_public(session, request.state.user, cid)


@router.put(
    "/dooblo/credentials",
    dependencies=[Depends(require_field_product_access)],
    summary="Guardar o actualizar credenciales Dooblo para la empresa (cifrado en base de datos).",
)
async def field_dooblo_put_credentials(
    request: Request,
    body: CompanyDoobloPutBody,
    company_id: int | None = Query(
        None, description="Superadmin: ID de la empresa. Obligatorio para rol 0."
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    return await upsert_dooblo_settings(
        session,
        request.state.user,
        cid,
        base_url=body.base_url,
        api_user=body.api_user,
        password=body.password,
    )


@router.get(
    "/qualtrics/status",
    dependencies=[Depends(require_field_product_access)],
    summary="Estado de credenciales Qualtrics para la empresa (sin exponer token); probe opcional.",
)
async def field_qualtrics_status(
    request: Request,
    company_id: int | None = Query(
        None, description="Superadmin: empresa objetivo. Otros roles usan su propia company."
    ),
    probe: bool = Query(
        False,
        description="Si true, valida token con GET /API/v3/surveys?pageSize=1 en el datacenter indicado.",
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    out = await get_qualtrics_settings_public(
        session, request.state.user, cid, probe_remote=probe
    )
    return out


@router.get(
    "/qualtrics/credentials",
    dependencies=[Depends(require_field_product_access)],
    summary="Ver configuración Qualtrics por empresa (sin token).",
)
async def field_qualtrics_get_credentials(
    request: Request,
    company_id: int | None = Query(
        None, description="Superadmin: ID de la empresa. Obligatorio para rol 0."
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    return await get_qualtrics_settings_public(session, request.state.user, cid)


@router.put(
    "/qualtrics/credentials",
    dependencies=[Depends(require_field_product_access)],
    summary="Guardar o actualizar credenciales Qualtrics (token cifrado en base de datos).",
)
async def field_qualtrics_put_credentials(
    request: Request,
    body: CompanyQualtricsPutBody,
    company_id: int | None = Query(
        None, description="Superadmin: ID de la empresa. Obligatorio para rol 0."
    ),
    session: AsyncSession = Depends(get_db),
):
    cid = _resolve_effective_company_id_for_field(request, company_id)
    return await upsert_qualtrics_settings(
        session,
        request.state.user,
        cid,
        base_url=body.base_url,
        api_token=body.api_token,
    )


@router.get(
    "/dooblo/catalog/customers",
    response_model=RemoteFieldCatalogPage,
    dependencies=[Depends(require_field_product_access)],
    summary="Catálogo paginado: clientes SurveyToGo (Customers) para el usuario API.",
)
async def field_dooblo_catalog_customers(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filtra por texto en nombre o ID (servidor)."),
    company_id: Optional[int] = Query(
        None, description="Superadmin: empresa cuyas credenciales Dooblo usar."
    ),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    return await list_dooblo_customers_catalog(
        creds, page=page, page_size=page_size, q=q
    )


@router.get(
    "/dooblo/catalog/organization-studio-projects",
    response_model=OrganizationStudioProjectsCatalogPage,
    dependencies=[Depends(require_field_product_access)],
    summary="Catálogo: proyectos Studio agregados por Customers × CustomerProjects (éxito parcial).",
)
async def field_dooblo_catalog_organization_studio_projects(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filtra por proyecto, ID o cliente (servidor)."),
    max_customers: int = Query(
        10,
        ge=1,
        le=200,
        description="Máximo de clientes SurveyToGo a recorrer. Use valores bajos (p.ej. 5) para aislar fallos o "
        "evitar timeout del proxy; suba si necesita cobertura mayor.",
    ),
    company_id: Optional[int] = Query(
        None, description="Superadmin: empresa cuyas credenciales Dooblo usar."
    ),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    return await list_dooblo_organization_studio_projects_catalog(
        creds,
        page=page,
        page_size=page_size,
        q=q,
        max_customers=max_customers,
    )


@router.get(
    "/dooblo/catalog/customer-projects",
    response_model=RemoteFieldCatalogPage,
    dependencies=[Depends(require_field_product_access)],
    summary="Catálogo paginado: proyectos Studio del cliente (CustomerProjects / SurveyToGo) con filtro q.",
)
async def field_dooblo_catalog_customer_projects(
    request: Request,
    customer_id: str = Query(
        ...,
        min_length=1,
        description="Customer ID en SurveyToGo (operation Customers). Obligatorio.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filtra por texto en nombre o ID (servidor)."),
    company_id: Optional[int] = Query(
        None, description="Superadmin: empresa cuyas credenciales Dooblo usar."
    ),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    return await list_dooblo_customer_projects_catalog(
        creds,
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        q=q,
    )


@router.get(
    "/dooblo/catalog/project-surveys",
    response_model=RemoteFieldCatalogPage,
    dependencies=[Depends(require_field_product_access)],
    summary="Catálogo paginado: encuestas de un proyecto Studio (ProjectSurveys) con filtro q.",
)
async def field_dooblo_catalog_project_surveys(
    request: Request,
    project_id: str = Query(
        ...,
        min_length=1,
        description="Studio ProjectID en la newapi Dooblo (mismo valor que ProjectSurveys).",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filtra por texto en nombre o SurveyID (servidor)."),
    company_id: Optional[int] = Query(
        None, description="Superadmin: empresa cuyas credenciales Dooblo usar."
    ),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    return await list_dooblo_project_surveys_catalog(
        creds,
        project_id=project_id.strip(),
        page=page,
        page_size=page_size,
        q=q,
    )


@router.get(
    "/dooblo/survey-interview-ids",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewIDs (lista de subject IDs bajo criterio / encuesta).",
)
async def field_dooblo_survey_interview_ids(
    request: Request,
    surveyID: str = Query(
        ..., description="Parámetro surveyIDs en newapi (ID o lista según documentación Dooblo)."
    ),
    company_id: int | None = Query(
        None, description="Superadmin: empresa cuyas credenciales Dooblo usar."
    ),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_survey_interview_ids(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey-interview-ids-by-modified",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewIDsByLastModified (sincronización por ventana de tiempo).",
)
async def field_dooblo_survey_interview_ids_by_modified(
    request: Request,
    surveyID: str = Query(..., description="Encuesta (surveyIDs en newapi)"),
    daysBack: Optional[int] = Query(None, ge=0, le=3650),
    fromDate: Optional[str] = None,
    toDate: Optional[str] = None,
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_survey_interview_ids_by_last_modified(
        surveyID, days_back=daysBack, from_date=fromDate, to_date=toDate, creds=creds
    )
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/project-surveys",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: ProjectSurveys (encuestas de un proyecto).",
)
async def field_dooblo_project_surveys(
    request: Request,
    projectID: str = Query(..., description="ID de proyecto en Studio / newapi"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_project_surveys(projectID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: Surveys (detalles de una encuesta).",
)
async def field_dooblo_survey_details(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta en SurveyToGo"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_survey_details(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/simple-survey-export",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SimpleSurveyExport (estructura de encuesta; preferible a GetSurveyXML).",
)
async def field_dooblo_simple_survey_export(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_simple_survey_export(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/simple-export",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SimpleExport (export tabular; subjectIDs separados por coma, máx. 99 por lote al consumir).",
)
async def field_dooblo_simple_export(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="IDs de sujeto separados por coma, ej. 101,102,103"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_simple_export(surveyID, subjectIDs, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/operation-data",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: OperationData (datos operacionales de entrevistas).",
)
async def field_dooblo_operation_data(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="IDs de sujeto separados por coma"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_operation_data(surveyID, subjectIDs, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey-interview-data",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewData (XML/JSON; hasta 99 subjectIDs por llamada).",
)
async def field_dooblo_survey_interview_data(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="Hasta 99 IDs separados por coma"),
    onlyHeaders: bool = Query(False, description="Solo cabeceras si aplica en newapi"),
    includeNulls: bool = Query(False, description="Incluir nulos en payload"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_survey_interview_data(
        surveyID,
        subjectIDs,
        only_headers=onlyHeaders,
        include_nulls=includeNulls,
        creds=creds,
    )
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/quotas-status",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: GetSurveyQuotasStatus (estado de cuotas por encuesta).",
)
async def field_dooblo_quotas_status(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_survey_quotas_status(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/quota-structure",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: QuotaStructure (malla de cuota).",
)
async def field_dooblo_quota_structure(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_quota_structure(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/handling-examples",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: HandlingExamples (totales de cuota en tabla).",
)
async def field_dooblo_handling_examples(
    request: Request,
    surveyID: str = Query(..., description="ID de encuesta"),
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    r = await dooblo.get_handling_examples(surveyID, creds=creds)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/surveyors-route",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: GetSurveyorsRoute (rutas GPS; suele requerir SurveyorName o GroupName).",
)
async def field_dooblo_surveyors_route(
    request: Request,
    surveyorName: Optional[str] = Query(None, description="Nombre de encuestado / surveyor (según doc)"),
    groupName: Optional[str] = Query(None, description="O grupo, según requisito newapi"),
    surveyID: Optional[str] = Query(None, description="Opcional, si aplica a la ruta"),
    fromDate: Optional[str] = None,
    toDate: Optional[str] = None,
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    try:
        r = await dooblo.get_surveyors_route(
            survey_id=surveyID,
            surveyor_name=surveyorName,
            group_name=groupName,
            from_date=fromDate,
            to_date=toDate,
            creds=creds,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/raw/{operation}",
    dependencies=[Depends(require_field_product_access)],
    summary="Proxy genérico (lista blanca): pasa query string a Dooblo newapi. Usar si el wrapper no expone aún un parámetro.",
)
async def field_dooblo_raw(
    operation: str,
    request: Request,
    company_id: int | None = Query(None, description="Superadmin: empresa (credenciales)."),
    session: AsyncSession = Depends(get_db),
):
    if operation not in DOOBLO_RAW_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"Operación no permitida. Permitidas: {', '.join(sorted(DOOBLO_RAW_ALLOWED))}.",
        )
    creds = await _dooblo_creds_for_request_or_503(session, request, company_id)
    # No reenviar `company_id` a Dooblo.
    params: dict = {
        k: v for k, v in dict(request.query_params).items() if k != "company_id"
    }
    r = await dooblo.dooblo_get(operation, params, creds=creds)
    return _dooblo_proxy(r)


@router.get("/access")
async def field_access_probe(request: Request, session: AsyncSession = Depends(get_db)):
    user = request.state.user
    if user.role == 0:
        return {"field_enabled": True, "scope": "global"}
    if user.company_id is None:
        return {"field_enabled": False, "scope": None}
    c = await session.get(Company, user.company_id)
    ok = c is not None and bool(c.siete_field_enabled)
    return {"field_enabled": ok, "scope": "company", "company_id": user.company_id}


@router.get(
    "/studies",
    response_model=list[FieldStudyPublic],
    dependencies=[Depends(require_field_product_access)],
)
async def list_studies(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: obligatorio."),
    client_id: Optional[int] = Query(None, description="Filtrar por cliente final."),
    session: AsyncSession = Depends(get_db),
):
    return await list_field_studies(
        session, request.state.user, company_id, client_id
    )


@router.post(
    "/studies",
    response_model=FieldStudyPublic,
    dependencies=[Depends(require_field_product_access)],
)
async def create_study(
    request: Request,
    body: FieldStudyCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_field_study(session, request.state.user, body)


@router.get(
    "/studies/{study_id}/brief",
    response_model=FieldStudyBriefPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Brief PRE-FIELD del estudio (lineage / snapshots)",
)
async def get_study_brief(
    study_id: int,
    request: Request,
    response: Response,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla Field."),
    session: AsyncSession = Depends(get_db),
):
    out = await get_field_study_brief_public(
        session, request.state.user, study_id, company_id
    )
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return out


@router.patch(
    "/studies/{study_id}/brief",
    response_model=FieldStudyBriefPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Actualizar payload/score del brief (no permite si ya aprobado)",
)
async def patch_study_brief(
    study_id: int,
    request: Request,
    response: Response,
    body: FieldStudyBriefPatch,
    company_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    out = await patch_field_study_brief(
        session, request.state.user, study_id, body, company_id
    )
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return out


@router.post(
    "/studies/{study_id}/brief/approve-internal",
    response_model=FieldStudyBriefPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Marcar brief aprobado internamente (gate opcional Readiness)",
)
async def approve_study_brief_internal_route(
    study_id: int,
    request: Request,
    response: Response,
    company_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    out = await approve_field_study_brief_internal(
        session, request.state.user, study_id, company_id
    )
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return out


@router.post(
    "/studies/{study_id}/brief/approve-client",
    response_model=FieldStudyBriefPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Marcar visto bueno cliente (B2B2B; requiere approved_internal)",
)
async def approve_study_brief_client_route(
    study_id: int,
    request: Request,
    response: Response,
    company_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    out = await approve_field_study_brief_client(
        session, request.state.user, study_id, company_id
    )
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return out


# --- PRE-FIELD: revisiones instrument_spec + validación schema (gobernanza previa al campo)


@router.post(
    "/instrument-spec/validate",
    response_model=InstrumentSpecValidationReport,
    dependencies=[Depends(require_field_product_access)],
    summary="Validar instrument_spec contra schema oficial (sin persistencia)",
    description=(
        "Ejecuta el mismo motor JSON Schema que Auto QA v1; útil para el Builder antes "
        "de guardar revisión o para pegados rápidos. Respuesta incluye `content_hash` "
        "canónico para auditoría."
    ),
)
async def validate_instrument_spec_http(
    request: Request,
    body: InstrumentSpecValidateBody,
):
    return await validate_instrument_spec_inline(request.state.user, body.spec)


@router.get(
    "/framework-templates",
    response_model=list[FieldFrameworkTemplatePublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Catálogo Framework Library (plantillas PRE-FIELD)",
    description=(
        "Plantillas metodológicas activas (`coverage_rules`, `stub_spec_json`). "
        "Filtro opcional por `study_type` alineado al enum de `instrument_spec`."
    ),
)
async def list_framework_templates(
    request: Request,
    study_type: Optional[str] = Query(
        None,
        description="Filtra por tipo de estudio exacto (p. ej. cx, ua, brand_tracking).",
    ),
    session: AsyncSession = Depends(get_db),
):
    if study_type is not None:
        st = study_type.strip().lower()
        if st not in FRAMEWORK_TEMPLATE_STUDY_TYPES:
            raise HTTPException(
                status_code=422,
                detail="study_type debe ser uno del enum instrument_spec (cx, ua, brand_tracking, …).",
            )
        study_type_norm = st
    else:
        study_type_norm = None
    return await list_field_framework_templates_for_api(
        session, request.state.user, study_type=study_type_norm
    )


@router.get(
    "/studies/{study_id}/instrument-revisions",
    response_model=list[FieldInstrumentRevisionPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Listar revisiones de instrumento del estudio",
)
async def list_study_instrument_revisions(
    study_id: int,
    request: Request,
    company_id: Optional[int] = Query(
        None,
        description="Rol 0: obligatorio si no hay empresa en el perfil; opcional si ya tiene empresa.",
    ),
    session: AsyncSession = Depends(get_db),
):
    return await list_instrument_revisions_for_study(
        session, request.state.user, study_id, company_id
    )


@router.post(
    "/studies/{study_id}/instrument-revisions",
    response_model=FieldInstrumentRevisionPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Crear revisión borrador (instrument_spec)",
    description=(
        "Crea una revisión `draft` versionada por `revision_label` único por estudio "
        "(auto `vN` si se omite). Si no envía `spec`, puede usar plantilla de catálogo con "
        "`framework_template_slug` (+ `framework_template_version`, por defecto `2026.1`) "
        "o la plantilla mínima interna. Si envía `spec` y un slug válido, persiste trazabilidad "
        "en `framework_template_id` como `slug@version`."
    ),
)
async def create_study_instrument_revision(
    study_id: int,
    request: Request,
    body: FieldInstrumentRevisionCreate,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await create_instrument_revision(
        session, request.state.user, study_id, body, company_id
    )


@router.get(
    "/instrument-revisions/{revision_id}",
    response_model=FieldInstrumentRevisionWithSpec,
    dependencies=[Depends(require_field_product_access)],
    summary="Detalle de revisión incluyendo instrument_spec completo",
)
async def get_instrument_revision_detail(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    pub, spec = await get_instrument_revision(
        session,
        request.state.user,
        revision_id,
        company_id,
        include_spec=True,
    )
    assert spec is not None
    return FieldInstrumentRevisionWithSpec(**{**pub.model_dump(), "spec": spec})


@router.patch(
    "/instrument-revisions/{revision_id}",
    response_model=FieldInstrumentRevisionPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Actualizar borrador (reemplazo de spec o metadata)",
    description="Solo revisiones `draft`. Para cerrar sin borrar: `status=archived`.",
)
async def patch_instrument_revision_http(
    revision_id: int,
    request: Request,
    body: FieldInstrumentRevisionPatch,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await patch_instrument_revision(
        session, request.state.user, revision_id, body, company_id
    )


@router.get(
    "/instrument-revisions/{revision_id}/framework-waivers",
    response_model=list[FieldFrameworkWaiverPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Listar waivers de framework ligados a esta revisión",
)
async def list_revision_framework_waivers(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla Field."),
    session: AsyncSession = Depends(get_db),
):
    return await list_framework_waivers_for_revision(
        session, request.state.user, revision_id, company_id
    )


@router.post(
    "/instrument-revisions/{revision_id}/framework-waivers",
    response_model=FieldFrameworkWaiverPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Registrar waiver explícito (solo revisión draft)",
)
async def create_revision_framework_waiver(
    revision_id: int,
    request: Request,
    body: FieldFrameworkWaiverCreate,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla Field."),
    session: AsyncSession = Depends(get_db),
):
    return await create_framework_waiver_for_revision(
        session, request.state.user, revision_id, body, company_id
    )


@router.post(
    "/instrument-revisions/{revision_id}/validate",
    response_model=FieldInstrumentRevisionValidateResponse,
    dependencies=[Depends(require_field_product_access)],
    summary="Validar revisión persistida y registrar auditoría schema",
    description=(
        "Ejecuta JSON Schema, guarda `last_validation_*` y devuelve informe completo. "
        "No sustituye Readiness Gate ni publicación en EMS."
    ),
)
async def validate_stored_instrument_revision(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await validate_instrument_revision_and_persist(
        session, request.state.user, revision_id, company_id
    )


@router.post(
    "/instrument-revisions/{revision_id}/qa-run",
    response_model=InstrumentQAExecuteResponse,
    dependencies=[Depends(require_field_product_access)],
    summary="Ejecutar motor QA_RULE_001–005 (bootstrap) y persistir corrida",
    description=(
        "Reglas determinísticas sobre `instrument_spec` vigente: doble varilla, leading/lexicón, "
        "cuotas, escalas y grafo de routing. Severidades STOP / FIX_NOW. "
        "Histórico en `field_instrument_qa_runs` (`source=instrument_qa_runtime`)."
    ),
)
async def run_instrument_revision_qa_bootstrap(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await execute_instrument_qa_bootstrap_run(
        session, request.state.user, revision_id, company_id
    )


@router.get(
    "/instrument-revisions/{revision_id}/qa-runs",
    response_model=list[FieldInstrumentQARunPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Historial de corridas QA bootstrap para la revisión",
)
async def list_instrument_revision_qa_runs(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    return await list_instrument_qa_runs(
        session, request.state.user, revision_id, company_id, limit=limit
    )


# --- Readiness Gate L4 (política, signatarios, firmas)


@router.get(
    "/readiness-policy",
    response_model=FieldReadinessPolicyPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Política Readiness de la empresa (bloqueos + roles exigidos)",
)
async def get_field_readiness_policy(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await get_readiness_policy_for_reader(
        session, request.state.user, company_id
    )


@router.put(
    "/readiness-policy",
    response_model=FieldReadinessPolicyPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Actualizar política Readiness (superadmin o gerente empresa)",
)
async def put_field_readiness_policy(
    request: Request,
    body: FieldReadinessPolicyUpsert,
    company_id: Optional[int] = Query(None, description="Rol 0: empresa objetivo."),
    session: AsyncSession = Depends(get_db),
):
    return await upsert_company_readiness_policy(
        session, request.state.user, company_id, body
    )


@router.get(
    "/readiness-signatories",
    response_model=list[FieldReadinessSignatoryPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Signatarios autorizados por rol (cuando ``enforce_signatory_grants``)",
)
async def get_field_readiness_signatories(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: empresa objetivo."),
    session: AsyncSession = Depends(get_db),
):
    return await list_readiness_signatories(session, request.state.user, company_id)


@router.post(
    "/readiness-signatories",
    response_model=FieldReadinessSignatoryPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Alta signatario (superadmin o gerente empresa)",
)
async def post_field_readiness_signatory(
    request: Request,
    body: FieldReadinessSignatoryCreate,
    company_id: Optional[int] = Query(None, description="Rol 0: empresa objetivo."),
    session: AsyncSession = Depends(get_db),
):
    return await create_readiness_signatory(
        session, request.state.user, company_id, body
    )


@router.delete(
    "/readiness-signatories/{signatory_id}",
    status_code=204,
    dependencies=[Depends(require_field_product_access)],
    summary="Baja lógica signatario",
)
async def delete_field_readiness_signatory(
    signatory_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: empresa objetivo."),
    session: AsyncSession = Depends(get_db),
):
    await soft_delete_readiness_signatory(
        session, request.state.user, company_id, signatory_id
    )


@router.get(
    "/instrument-revisions/{revision_id}/readiness",
    response_model=ReadinessGatePublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Estado Readiness agregado (gates + firmas + política efectiva)",
)
async def get_instrument_revision_readiness(
    revision_id: int,
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await get_readiness_for_revision(
        session, request.state.user, revision_id, company_id
    )


@router.post(
    "/instrument-revisions/{revision_id}/readiness-sign",
    response_model=ReadinessSignResult,
    dependencies=[Depends(require_field_product_access)],
    summary="Registrar firma nominal L4 (snapshot hash + último QA run)",
    description=(
        "Requiere gates en verde según política. Si tras firmar se cumplen todos los roles "
        "requeridos, la revisión pasa a estado ``approved``."
    ),
)
async def post_instrument_revision_readiness_sign(
    revision_id: int,
    request: Request,
    body: ReadinessSignBody,
    company_id: Optional[int] = Query(None, description="Rol 0: misma regla que otros listados Field."),
    session: AsyncSession = Depends(get_db),
):
    return await sign_readiness_for_revision(
        session, request.state.user, revision_id, body, company_id
    )


@router.get(
    "/projects",
    response_model=list[FieldProjectPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Listar proyectos Field (metadatos CRUD)",
    description=(
        "Respuesta plana: nombre, cliente, estado, `ingest_mode`, fechas. "
        "Para **centro de mando** (semáforo `health`, KPIs, conteos de hallazgos, vínculos Dooblo) "
        "usar el mismo prefijo y query params con **GET /field/projects/overview**."
    ),
)
async def list_projects(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: obligatorio."),
    client_id: Optional[int] = Query(None, description="Filtrar por cliente final."),
    session: AsyncSession = Depends(get_db),
):
    return await list_field_projects(
        session, request.state.user, company_id, client_id
    )


@router.get(
    "/projects/overview",
    response_model=list[FieldProjectOverviewRow],
    dependencies=[Depends(require_field_product_access)],
    summary="Resumen multi-proyecto: KPIs, hallazgos abiertos, vínculos Dooblo y semáforo de salud.",
)
async def list_projects_overview(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: obligatorio."),
    client_id: Optional[int] = Query(None, description="Filtrar por cliente final (opcional)."),
    session: AsyncSession = Depends(get_db),
):
    return await list_field_projects_overview(
        session, request.state.user, company_id, client_id
    )


@router.post(
    "/projects",
    response_model=FieldProjectPublic,
    dependencies=[Depends(require_field_product_access)],
)
async def create_project(
    request: Request,
    body: FieldProjectCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_field_project(session, request.state.user, body)


@router.patch(
    "/projects/{project_id}",
    response_model=FieldProjectPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Actualización parcial del proyecto (p. ej. study_id para proyectos legacy).",
)
async def patch_project(
    project_id: int,
    request: Request,
    body: FieldProjectPatch,
    session: AsyncSession = Depends(get_db),
):
    return await patch_field_project(session, request.state.user, project_id, body)


@router.get(
    "/projects/{project_id}/overview",
    response_model=FieldProjectOverviewRow,
    dependencies=[Depends(require_field_product_access)],
    summary="Clic 3: salud del proyecto (semáforo, KPIs, conteos, muestra de hallazgos abiertos) en una sola respuesta.",
)
async def get_project_overview_drilldown(
    project_id: int,
    request: Request,
    top_findings_limit: int = Query(
        8,
        ge=0,
        le=50,
        description="Hallazgos abiertos más recientes/severos; 0 omite la lista.",
    ),
    session: AsyncSession = Depends(get_db),
):
    return await get_field_project_overview_drilldown(
        session, request.state.user, project_id, top_findings_limit=top_findings_limit
    )


@router.post(
    "/projects/{project_id}/sync",
    response_model=FieldProjectSyncResponse,
    dependencies=[Depends(require_field_product_access)],
    summary="Sync MVP: materializa encuestas Field desde fuentes Dooblo activas y emite KPI completion_rate (proxy).",
)
async def post_project_execution_sync(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await sync_field_project_from_sources(session, request.state.user, project_id)


@router.get(
    "/projects/{project_id}/kpis",
    response_model=list[FieldMetricPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Último valor conocido por metric_code (MVP: completion_rate desde sync).",
)
async def get_project_kpis(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await list_project_kpis(session, request.state.user, project_id)


@router.get(
    "/projects/{project_id}/surveys",
    response_model=list[FieldSurveyPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Encuestas canónicas Field bajo el proyecto (post-sync).",
)
async def get_project_field_surveys(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await list_project_surveys(session, request.state.user, project_id)


@router.get(
    "/projects/{project_id}/decision-layer/external-sources",
    response_model=list[FieldProjectExternalSourcePublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Mapeos canónicos a orígenes (Dooblo, CSV, manual).",
)
async def get_project_external_sources(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await list_external_sources(session, request.state.user, project_id)


@router.get(
    "/projects/{project_id}/decision-layer/policy-sets",
    response_model=list[FieldPolicySetPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Políticas/umbrales versionados del proyecto (reglas de negocio auditable).",
)
async def get_project_policy_sets(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await list_policy_sets(session, request.state.user, project_id)


@router.get(
    "/projects/{project_id}/operational-snapshot",
    response_model=FieldOperationalSnapshotPublic | None,
    dependencies=[Depends(require_field_product_access)],
    summary="Proyección de estado (cuota, GPS, flags) si existe; aún no calculada = null.",
)
async def get_project_operational_snapshot(
    project_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await get_operational_snapshot(session, request.state.user, project_id)


@router.post(
    "/projects/{project_id}/decision-layer/external-sources",
    response_model=FieldProjectExternalSourcePublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Crear mapeo a origen (Dooblo, CSV, manual, etc.).",
)
async def post_project_external_source(
    project_id: int,
    request: Request,
    body: FieldProjectExternalSourceCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_external_source(session, request.state.user, project_id, body)


@router.post(
    "/projects/{project_id}/decision-layer/policy-sets",
    response_model=FieldPolicySetPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Crear nueva versión de política (versión = max+1 en el proyecto).",
)
async def post_project_policy_set(
    project_id: int,
    request: Request,
    body: FieldPolicySetCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_policy_set(session, request.state.user, project_id, body)


@router.get(
    "/projects/{project_id}/decision-layer/sync-runs",
    response_model=list[FieldSyncRunPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Corridas técnicas de sync/análisis (incl. field_analysis).",
)
async def get_project_sync_runs(
    project_id: int,
    request: Request,
    limit: int = Query(30, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    return await list_sync_runs(session, request.state.user, project_id, limit=limit)


@router.post(
    "/projects/{project_id}/decision-layer/dooblo-analyze",
    response_model=FieldSyncRunPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Encolar análisis Dooblo (cuota + reglas) de forma asíncrona. Idempotente por idempotency_key.",
)
async def post_project_dooblo_analyze(
    project_id: int,
    request: Request,
    body: DoobloAnalysisRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    public, created = await create_sync_run_for_dooblo_analysis(
        session, request.state.user, project_id, body
    )
    if created and public.id is not None:
        background_tasks.add_task(run_dooblo_analysis_task, public.id)
    return public


@router.get(
    "/projects/{project_id}/decision-layer/findings",
    response_model=list[FieldFindingPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Hallazgos (CSV y capa de decisión); filtro opcional por source=.",
)
async def get_project_all_findings(
    project_id: int,
    request: Request,
    source: Optional[str] = Query(None, description="Ej. dooblo_analysis, csv"),
    limit: int = Query(200, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await list_project_findings(
        session, request.state.user, project_id, source=source, limit=limit
    )


@router.patch(
    "/projects/{project_id}/decision-layer/findings/{finding_id}/approval",
    response_model=FieldFindingPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Aprobar / rechazar / pending un hallazgo (gobernanza de decisión).",
)
async def patch_finding_approval(
    project_id: int,
    finding_id: int,
    request: Request,
    body: FieldFindingApprovalBody,
    session: AsyncSession = Depends(get_db),
):
    return await set_finding_approval(
        session, request.state.user, project_id, finding_id, body
    )


@router.get(
    "/projects/{project_id}/decision-layer/findings/{finding_id}/decision-log",
    response_model=list[FieldFindingDecisionLogPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Historial auditable de decisiones (cambios de aprobación) sobre un hallazgo.",
)
async def get_finding_decision_log(
    project_id: int,
    finding_id: int,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await list_finding_decision_log(
        session, request.state.user, project_id, finding_id, limit=limit
    )


@router.post(
    "/projects/{project_id}/import",
    response_model=FieldImportRunPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Importar CSV formato 2026.1 (validación + registro de corrida)",
)
async def import_project_csv(
    project_id: int,
    request: Request,
    file: UploadFile = File(..., description="Archivo .csv UTF-8"),
    session: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    run = await import_field_csv_2026_1(session, request.state.user, project_id, raw)
    return FieldImportRunPublic.model_validate(run)


@router.get(
    "/projects/{project_id}/import-runs",
    response_model=list[FieldImportRunPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Corridas de import (Execution Ledger)",
)
async def get_project_import_runs(
    project_id: int,
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    return await list_import_runs_for_project(
        session, request.state.user, project_id, limit=limit
    )


@router.get(
    "/projects/{project_id}/import-runs/{run_id}/rows",
    response_model=list[FieldImportRowPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Filas materializadas de una corrida",
)
async def get_import_run_rows(
    project_id: int,
    run_id: int,
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await list_rows_for_run(
        session, request.state.user, project_id, run_id, offset=offset, limit=limit
    )


@router.get(
    "/projects/{project_id}/import-runs/{run_id}/findings",
    response_model=list[FieldFindingPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Hallazgos QC de una corrida",
)
async def get_import_run_findings(
    project_id: int,
    run_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    return await list_findings_for_run(session, request.state.user, project_id, run_id)


@router.get(
    "/projects/{project_id}/ledger-events",
    response_model=list[FieldLedgerEventPublic],
    dependencies=[Depends(require_field_product_access)],
    summary="Eventos de ledger del proyecto",
)
async def get_project_ledger_events(
    project_id: int,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    return await list_ledger_events_for_project(
        session, request.state.user, project_id, limit=limit
    )
