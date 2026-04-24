"""
Siete Field — proyectos de control de levantamiento (MVP interno, CSV-ready).

Prefijo: `/api/v1/field`
"""

from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import Company
from app.models.field_ledger_model import (
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
    FieldProjectPublic,
)
from app.services.field_decision_services import (
    create_external_source,
    create_policy_set,
    create_sync_run_for_dooblo_analysis,
    get_operational_snapshot,
    list_external_sources,
    list_policy_sets,
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
from app.services.field_project_services import create_field_project, list_field_projects
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.field_access import require_field_product_access
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


def _dooblo_require_config() -> None:
    if not dooblo.dooblo_configured():
        raise HTTPException(
            status_code=503,
            detail="Dooblo no está configurado (DOOBLO_BASE_URL, DOOBLO_USER, DOOBLO_PASSWORD).",
        )


def _dooblo_proxy(r: httpx.Response) -> dict:
    return httpx_response_to_proxy_dict(r)


@router.get(
    "/dooblo/status",
    dependencies=[Depends(require_field_product_access)],
    summary="Indica si el servidor tiene credenciales Dooblo (sin exponer secretos).",
)
async def field_dooblo_status():
    return {"dooblo_configured": dooblo.dooblo_configured()}


@router.get(
    "/dooblo/survey-interview-ids",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewIDs (lista de subject IDs bajo criterio / encuesta).",
)
async def field_dooblo_survey_interview_ids(
    surveyID: str = Query(
        ..., description="Parámetro surveyIDs en newapi (ID o lista según documentación Dooblo)."
    ),
):
    _dooblo_require_config()
    r = await dooblo.get_survey_interview_ids(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey-interview-ids-by-modified",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewIDsByLastModified (sincronización por ventana de tiempo).",
)
async def field_dooblo_survey_interview_ids_by_modified(
    surveyID: str = Query(..., description="Encuesta (surveyIDs en newapi)"),
    daysBack: Optional[int] = Query(None, ge=0, le=3650),
    fromDate: Optional[str] = None,
    toDate: Optional[str] = None,
):
    _dooblo_require_config()
    r = await dooblo.get_survey_interview_ids_by_last_modified(
        surveyID, days_back=daysBack, from_date=fromDate, to_date=toDate
    )
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/project-surveys",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: ProjectSurveys (encuestas de un proyecto).",
)
async def field_dooblo_project_surveys(
    projectID: str = Query(..., description="ID de proyecto en Studio / newapi"),
):
    _dooblo_require_config()
    r = await dooblo.get_project_surveys(projectID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: Surveys (detalles de una encuesta).",
)
async def field_dooblo_survey_details(
    surveyID: str = Query(..., description="ID de encuesta en SurveyToGo"),
):
    _dooblo_require_config()
    r = await dooblo.get_survey_details(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/simple-survey-export",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SimpleSurveyExport (estructura de encuesta; preferible a GetSurveyXML).",
)
async def field_dooblo_simple_survey_export(
    surveyID: str = Query(..., description="ID de encuesta"),
):
    _dooblo_require_config()
    r = await dooblo.get_simple_survey_export(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/simple-export",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SimpleExport (export tabular; subjectIDs separados por coma, máx. 99 por lote al consumir).",
)
async def field_dooblo_simple_export(
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="IDs de sujeto separados por coma, ej. 101,102,103"),
):
    _dooblo_require_config()
    r = await dooblo.get_simple_export(surveyID, subjectIDs)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/operation-data",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: OperationData (datos operacionales de entrevistas).",
)
async def field_dooblo_operation_data(
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="IDs de sujeto separados por coma"),
):
    _dooblo_require_config()
    r = await dooblo.get_operation_data(surveyID, subjectIDs)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/survey-interview-data",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: SurveyInterviewData (XML/JSON; hasta 99 subjectIDs por llamada).",
)
async def field_dooblo_survey_interview_data(
    surveyID: str = Query(..., description="ID de encuesta"),
    subjectIDs: str = Query(..., description="Hasta 99 IDs separados por coma"),
    onlyHeaders: bool = Query(False, description="Solo cabeceras si aplica en newapi"),
    includeNulls: bool = Query(False, description="Incluir nulos en payload"),
):
    _dooblo_require_config()
    r = await dooblo.get_survey_interview_data(
        surveyID, subjectIDs, only_headers=onlyHeaders, include_nulls=includeNulls
    )
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/quotas-status",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: GetSurveyQuotasStatus (estado de cuotas por encuesta).",
)
async def field_dooblo_quotas_status(
    surveyID: str = Query(..., description="ID de encuesta"),
):
    _dooblo_require_config()
    r = await dooblo.get_survey_quotas_status(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/quota-structure",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: QuotaStructure (malla de cuota).",
)
async def field_dooblo_quota_structure(
    surveyID: str = Query(..., description="ID de encuesta"),
):
    _dooblo_require_config()
    r = await dooblo.get_quota_structure(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/handling-examples",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: HandlingExamples (totales de cuota en tabla).",
)
async def field_dooblo_handling_examples(
    surveyID: str = Query(..., description="ID de encuesta"),
):
    _dooblo_require_config()
    r = await dooblo.get_handling_examples(surveyID)
    return _dooblo_proxy(r)


@router.get(
    "/dooblo/surveyors-route",
    dependencies=[Depends(require_field_product_access)],
    summary="Dooblo: GetSurveyorsRoute (rutas GPS; suele requerir SurveyorName o GroupName).",
)
async def field_dooblo_surveyors_route(
    surveyorName: Optional[str] = Query(None, description="Nombre de encuestado / surveyor (según doc)"),
    groupName: Optional[str] = Query(None, description="O grupo, según requisito newapi"),
    surveyID: Optional[str] = Query(None, description="Opcional, si aplica a la ruta"),
    fromDate: Optional[str] = None,
    toDate: Optional[str] = None,
):
    _dooblo_require_config()
    try:
        r = await dooblo.get_surveyors_route(
            survey_id=surveyID,
            surveyor_name=surveyorName,
            group_name=groupName,
            from_date=fromDate,
            to_date=toDate,
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
):
    _dooblo_require_config()
    if operation not in DOOBLO_RAW_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"Operación no permitida. Permitidas: {', '.join(sorted(DOOBLO_RAW_ALLOWED))}.",
        )
    # Query plana: claves repetidas, última gana (suficiente para la mayoría de llamadas).
    params: dict = dict(request.query_params)
    r = await dooblo.dooblo_get(operation, params)
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
    "/projects",
    response_model=list[FieldProjectPublic],
    dependencies=[Depends(require_field_product_access)],
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
