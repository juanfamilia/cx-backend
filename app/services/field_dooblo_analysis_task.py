"""
Tarea de análisis Dooblo (async, post-request): lee cuota, aplica reglas, escribe
snapshot e idempotency findings. Invocable desde FastAPI BackgroundTasks.
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.integrations import dooblo_client as dooblo
from app.services.company_dooblo_service import get_dooblo_creds_for_company
from app.integrations.field_decision_engine import (
    build_findings_from_quota_response,
    CODE_NO_SURVEY,
)
from app.integrations.dooblo_serialize import httpx_response_to_proxy_dict
from app.models.field_decision_model import (
    SOURCE_TYPE_DOOBLO,
    SOURCE_TYPE_DOOBLO_ANALYSIS,
    FieldOperationalSnapshot,
    FieldPolicySet,
    FieldProjectExternalSource,
    FieldSyncRun,
    RUN_KIND_FIELD_ANALYSIS,
    SYNC_RUN_COMPLETED,
    SYNC_RUN_FAILED,
    SYNC_RUN_PENDING,
    SYNC_RUN_PROCESSING,
)
from app.models.field_ledger_model import FieldFinding


def _utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def run_dooblo_analysis_task(sync_run_id: int) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await _process_sync_run(session, sync_run_id)
        except Exception:  # noqa: BLE001 — marcar run fallida con trazas
            await session.rollback()
            async with AsyncSessionLocal() as session2:
                r = await session2.get(FieldSyncRun, sync_run_id)
                if r is not None and r.status in (SYNC_RUN_PENDING, SYNC_RUN_PROCESSING):
                    r.status = SYNC_RUN_FAILED
                    r.error_summary = traceback.format_exc()[:20000]
                    r.completed_at = _utc_naive()
                    await session2.commit()


async def _process_sync_run(session: AsyncSession, sync_run_id: int) -> None:
    run = await session.get(FieldSyncRun, sync_run_id)
    if run is None or run.run_kind != RUN_KIND_FIELD_ANALYSIS:
        return
    if run.status in (SYNC_RUN_COMPLETED, SYNC_RUN_FAILED):
        return

    run.status = SYNC_RUN_PROCESSING
    run.started_at = run.started_at or _utc_naive()
    await session.commit()

    run = await session.get(FieldSyncRun, sync_run_id)
    assert run is not None  # nosec

    creds = await get_dooblo_creds_for_company(session, run.company_id)
    if creds is None:
        run.status = SYNC_RUN_FAILED
        run.error_summary = (
            "Dooblo no está configurado para esta empresa (guarde credenciales en Field) "
            "ni a nivel de servidor (DOOBLO_*)."
        )
        run.completed_at = _utc_naive()
        await session.commit()
        return

    # Fuente: explícita o primera dooblo activa con survey
    src: FieldProjectExternalSource | None = None
    if run.field_project_external_source_id:
        src = await session.get(FieldProjectExternalSource, run.field_project_external_source_id)
    if src is None:
        res = await session.execute(
            select(FieldProjectExternalSource)
            .where(
                FieldProjectExternalSource.field_project_id == run.field_project_id,
                FieldProjectExternalSource.is_active,
                FieldProjectExternalSource.source_type == SOURCE_TYPE_DOOBLO,
            )
            .order_by(FieldProjectExternalSource.id.desc())
        )
        src = res.scalars().first()

    if src is None or not (src.external_survey_id and str(src.external_survey_id).strip()):
        run.status = SYNC_RUN_FAILED
        run.error_summary = "No hay FieldProjectExternalSource dooblo con external_survey_id."
        run.completed_at = _utc_naive()
        await _insert_no_survey_finding(session, run)
        await session.commit()
        return

    policy: FieldPolicySet | None = None
    if run.field_policy_set_id:
        policy = await session.get(FieldPolicySet, run.field_policy_set_id)
    if policy is None:
        res = await session.execute(
            select(FieldPolicySet)
            .where(FieldPolicySet.field_project_id == run.field_project_id)
            .order_by(FieldPolicySet.version.desc())
        )
        policy = res.scalars().first()

    policy_config = (policy.config if policy is not None else {}) or {}
    policy_id = policy.id if policy else None

    survey_id = str(src.external_survey_id).strip()
    r_http = await dooblo.get_survey_quotas_status(survey_id, creds=creds)
    proxy = httpx_response_to_proxy_dict(r_http)
    upstream = int(proxy.get("upstream_status") or 0)
    quota_payload = proxy.get("data")
    if quota_payload is None and "raw" in proxy:
        quota_payload = {"raw": proxy.get("raw")}

    res_os = await session.execute(
        select(FieldOperationalSnapshot).where(
            FieldOperationalSnapshot.field_project_id == run.field_project_id
        )
    )
    os_row = res_os.scalars().first()
    q_state: dict = {"getSurveyQuotasStatus": proxy}
    if os_row is None:
        os_row = FieldOperationalSnapshot(
            field_project_id=run.field_project_id,
            field_sync_run_id=run.id,
            field_policy_set_id=policy_id,
            quotas_state=q_state,
            field_status={"source_external_id": src.id, "external_survey_id": survey_id},
        )
        session.add(os_row)
    else:
        os_row.field_sync_run_id = run.id
        os_row.field_policy_set_id = policy_id
        os_row.quotas_state = q_state
        os_row.last_calculated_at = _utc_naive()
        if os_row.field_status and isinstance(os_row.field_status, dict):
            new_fs = {**os_row.field_status, "source_external_id": src.id, "external_survey_id": survey_id}
            os_row.field_status = new_fs
        else:
            os_row.field_status = {"source_external_id": src.id, "external_survey_id": survey_id}

    drafts = build_findings_from_quota_response(
        upstream_status=upstream,
        quota_payload=quota_payload,
        policy_config=policy_config,
        sync_run_id=run.id,
    )
    for d in drafts:
        ikey = d["idempotency_key"]
        existing = await session.execute(
            select(FieldFinding.id).where(
                FieldFinding.field_project_id == run.field_project_id,
                FieldFinding.idempotency_key == ikey,
            )
        )
        if existing.first():
            continue
        session.add(
            FieldFinding(
                field_project_id=run.field_project_id,
                field_import_run_id=None,
                field_sync_run_id=run.id,
                field_policy_set_id=policy_id,
                idempotency_key=ikey,
                source=SOURCE_TYPE_DOOBLO_ANALYSIS,
                code=d["code"],
                severity=d["severity"],
                case_id=None,
                wave_id=src.wave_id,
                message=d["message"],
                explanation=d.get("explanation"),
                recommendation=d.get("recommendation"),
                evidence=d.get("evidence"),
            )
        )

    run.status = SYNC_RUN_COMPLETED
    run.error_summary = None
    run.total_records = 1
    run.completed_at = _utc_naive()
    if policy:
        run.field_policy_set_id = policy.id
    run.field_project_external_source_id = src.id
    await session.commit()


async def _insert_no_survey_finding(session: AsyncSession, run: FieldSyncRun) -> None:
    ikey = f"dec:sync{run.id}:NO_SURVEY"
    existing = await session.execute(
        select(FieldFinding.id).where(
            FieldFinding.field_project_id == run.field_project_id,
            FieldFinding.idempotency_key == ikey,
        )
    )
    if existing.first():
        return
    session.add(
        FieldFinding(
            field_project_id=run.field_project_id,
            field_import_run_id=None,
            field_sync_run_id=run.id,
            field_policy_set_id=run.field_policy_set_id,
            idempotency_key=ikey,
            source=SOURCE_TYPE_DOOBLO_ANALYSIS,
            code=CODE_NO_SURVEY,
            severity="error",
            case_id=None,
            wave_id=None,
            message="Falta mapeo Dooblo (external_survey_id) o fuente inactiva.",
            explanation="La capa de decisión requiere al menos un FieldProjectExternalSource dooblo con survey.",
            recommendation="Cree el mapeo vía API o asegure activar y enlazar el survey correcto.",
            evidence=None,
        )
    )
