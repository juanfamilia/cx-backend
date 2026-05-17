"""
Tarea de análisis Dooblo (async, post-request): lee cuota, aplica reglas, escribe
snapshot e idempotency findings. Invocable desde FastAPI BackgroundTasks.
"""

from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.integrations import dooblo_client as dooblo
from app.services.company_dooblo_service import get_dooblo_creds_for_company
from app.integrations.field_decision_engine import collect_dooblo_analysis_finding_drafts
from app.integrations.field_finding_codes import DOOBLO_NO_SURVEY_ID
from app.integrations.dooblo_serialize import httpx_response_to_proxy_dict
from app.integrations.field_dooblo_gps_quality import (
    gps_params_from_policy,
    summarize_gps_rows,
)
from app.integrations.field_dooblo_response_quality import (
    duration_bounds_from_policy,
    extract_subject_ids_from_survey_interview_payload,
    flatten_tabular_rows,
    straight_lining_params_from_policy,
    summarize_response_quality_rows,
)
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
from app.models.field_project_model import FieldProject
from app.platform_intelligence.signals_service import emit_platform_signal_safe


def _utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _fetch_dooblo_tabular_sample(
    *,
    survey_id: str,
    creds: dooblo.DoobloCreds,
    policy_config: dict[str, Any],
) -> dict[str, Any]:
    """~2 req/s: espera entre llamadas Dooblo y muestra acotada por política."""
    await asyncio.sleep(0.55)
    r_iv = await dooblo.get_survey_interview_ids(survey_id, creds=creds)
    proxy_iv = httpx_response_to_proxy_dict(r_iv)
    iv_status = int(proxy_iv.get("upstream_status") or 0)
    iv_body = proxy_iv.get("data")
    if iv_body is None and proxy_iv.get("raw") is not None:
        iv_body = proxy_iv.get("raw")
    ids = extract_subject_ids_from_survey_interview_payload(iv_body)

    max_subj = policy_config.get("dooblo_tabular_max_subjects")
    if max_subj is None:
        max_subj = policy_config.get("response_quality_max_subjects", 30)
    try:
        max_subj_i = max(1, min(200, int(max_subj)))
    except (TypeError, ValueError):
        max_subj_i = 30
    ids = ids[:max_subj_i]

    op_status: int | None = None
    simple_status: int | None = None
    rows: list[dict[str, Any]] = []
    used_fb = False

    if ids and 200 <= iv_status < 300:
        await asyncio.sleep(0.55)
        subject_csv = ",".join(ids)
        r_op = await dooblo.get_operation_data(survey_id, subject_csv, creds=creds)
        proxy_op = httpx_response_to_proxy_dict(r_op)
        op_status = int(proxy_op.get("upstream_status") or 0)
        op_body = proxy_op.get("data")
        rows = flatten_tabular_rows(op_body if op_body is not None else {})
        if not rows and 200 <= op_status < 300:
            await asyncio.sleep(0.55)
            r_se = await dooblo.get_simple_export(survey_id, subject_csv, creds=creds)
            proxy_se = httpx_response_to_proxy_dict(r_se)
            simple_status = int(proxy_se.get("upstream_status") or 0)
            se_body = proxy_se.get("data")
            rows = flatten_tabular_rows(se_body if se_body is not None else {})
            used_fb = True

    rq_on = policy_config.get("response_quality_enabled", False)
    if rq_on:
        d_lo, d_hi = duration_bounds_from_policy(policy_config)
        st_en, st_min, st_max, st_cells = straight_lining_params_from_policy(policy_config)
        summary = summarize_response_quality_rows(
            rows,
            duration_min=d_lo,
            duration_max=d_hi,
            straight_enabled=st_en,
            scale_min=st_min,
            scale_max=st_max,
            straight_min_cells=st_cells,
        )
    else:
        summary = summarize_response_quality_rows(
            rows,
            duration_min=None,
            duration_max=None,
            straight_enabled=False,
            scale_min=1.0,
            scale_max=5.0,
            straight_min_cells=999,
        )

    gps_summary = None
    if policy_config.get("gps_quality_enabled", False):
        max_km, null_flag, column_pairs = gps_params_from_policy(policy_config)
        gps_summary = summarize_gps_rows(
            rows,
            max_internal_distance_km=max_km,
            flag_null_island=null_flag,
            column_pairs=column_pairs,
        )

    return {
        "interview_ids_status": iv_status,
        "operation_status": op_status,
        "simple_export_status": simple_status,
        "subject_sample_size": len(ids),
        "used_simple_export_fallback": used_fb,
        "summary": summary,
        "gps_summary": gps_summary,
    }


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

    tabular_sample_ctx: dict[str, Any] | None = None
    if policy_config.get("response_quality_enabled", False) or policy_config.get(
        "gps_quality_enabled", False
    ):
        tabular_sample_ctx = await _fetch_dooblo_tabular_sample(
            survey_id=survey_id,
            creds=creds,
            policy_config=policy_config,
        )

    res_os = await session.execute(
        select(FieldOperationalSnapshot).where(
            FieldOperationalSnapshot.field_project_id == run.field_project_id
        )
    )
    os_row = res_os.scalars().first()
    q_state: dict = {"getSurveyQuotasStatus": proxy}
    if tabular_sample_ctx is not None:
        rq_blob = {
            "interview_ids_status": tabular_sample_ctx["interview_ids_status"],
            "operation_status": tabular_sample_ctx["operation_status"],
            "simple_export_status": tabular_sample_ctx["simple_export_status"],
            "subject_sample_size": tabular_sample_ctx["subject_sample_size"],
            "used_simple_export_fallback": tabular_sample_ctx["used_simple_export_fallback"],
            "summary": tabular_sample_ctx["summary"],
            "gps_summary": tabular_sample_ctx.get("gps_summary"),
        }
        q_state["response_quality"] = rq_blob

    if os_row is None:
        os_row = FieldOperationalSnapshot(
            field_project_id=run.field_project_id,
            field_sync_run_id=run.id,
            field_policy_set_id=policy_id,
            quotas_state=q_state,
            field_status=(
                {
                    "source_external_id": src.id,
                    "external_survey_id": survey_id,
                    **({"response_quality": q_state["response_quality"]} if tabular_sample_ctx else {}),
                }
            ),
        )
        session.add(os_row)
    else:
        os_row.field_sync_run_id = run.id
        os_row.field_policy_set_id = policy_id
        os_row.quotas_state = q_state
        os_row.last_calculated_at = _utc_naive()
        base_fs = (
            {**os_row.field_status, "source_external_id": src.id, "external_survey_id": survey_id}
            if os_row.field_status and isinstance(os_row.field_status, dict)
            else {"source_external_id": src.id, "external_survey_id": survey_id}
        )
        if tabular_sample_ctx is not None:
            base_fs["response_quality"] = q_state["response_quality"]
        os_row.field_status = base_fs

    drafts = collect_dooblo_analysis_finding_drafts(
        upstream_status=upstream,
        quota_payload=quota_payload,
        policy_config=policy_config,
        sync_run_id=run.id,
        tabular_sample=tabular_sample_ctx,
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
    rq_rows = (
        int(tabular_sample_ctx["summary"].get("row_count") or 0)
        if tabular_sample_ctx is not None
        else 0
    )
    run.total_records = 1 + rq_rows
    run.completed_at = _utc_naive()
    if policy:
        run.field_policy_set_id = policy.id
    run.field_project_external_source_id = src.id
    await session.commit()

    proj = await session.get(FieldProject, run.field_project_id)
    study_id = proj.study_id if proj else None
    await emit_platform_signal_safe(
        session,
        company_id=run.company_id,
        user_id=None,
        source_domain="field",
        signal_code="field.dooblo_analysis_completed",
        summary=f"Field: análisis Dooblo completado (sync run {run.id})",
        severity="low",
        payload={
            "field_sync_run_id": run.id,
            "field_project_id": run.field_project_id,
            "total_records": run.total_records,
        },
        field_project_id=run.field_project_id,
        field_study_id=study_id,
    )


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
            code=DOOBLO_NO_SURVEY_ID,
            severity="error",
            case_id=None,
            wave_id=None,
            message="Falta mapeo Dooblo (external_survey_id) o fuente inactiva.",
            explanation="La capa de decisión requiere al menos un FieldProjectExternalSource dooblo con survey.",
            recommendation="Cree el mapeo vía API o asegure activar y enlazar el survey correcto.",
            evidence=None,
        )
    )
