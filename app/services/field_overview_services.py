"""Listado agregado de proyectos Field para vista ejecutiva (sin N+1 en el cliente)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.end_client_model import EndClient
from app.models.field_decision_model import (
    SOURCE_TYPE_DOOBLO,
    RUN_KIND_FIELD_ANALYSIS,
    FieldOperationalSnapshot,
    FieldProjectExternalSource,
    FieldSyncRun,
)
from app.models.field_execution_model import FieldMetric, FieldMetricPublic, FieldSurvey
from app.models.field_ledger_model import FieldFinding, FieldFindingPublic
from app.models.field_overview_model import FieldProjectOverviewRow
from app.models.field_project_model import FieldImportRun, FieldProjectPublic
from app.models.field_study_model import FieldStudy
from app.models.user_model import User
from app.services.field_project_services import (
    _assert_project_company_access,
    _get_field_project_writable,
    assert_field_staff,
    list_field_projects,
)


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_stale(dt: datetime | None, days: int) -> bool:
    if dt is None:
        return True
    return dt < _utc_naive_now() - timedelta(days=days)


def _quota_signals(snapshot: FieldOperationalSnapshot | None) -> tuple[bool | None, int | None]:
    """Devuelve (upstream_http_ok_guess, tabular_row_count si existe)."""
    if snapshot is None or not snapshot.quotas_state:
        return None, None
    qs = snapshot.quotas_state
    gsq = qs.get("getSurveyQuotasStatus") if isinstance(qs, dict) else None
    upstream_ok: bool | None = None
    if isinstance(gsq, dict):
        try:
            code = int(gsq.get("upstream_status") or 0)
            upstream_ok = 200 <= code < 300
        except (TypeError, ValueError):
            upstream_ok = None
    row_count: int | None = None
    rq = qs.get("response_quality") if isinstance(qs, dict) else None
    if isinstance(rq, dict):
        summary = rq.get("summary")
        if isinstance(summary, dict):
            try:
                row_count = int(summary.get("row_count") or 0)
            except (TypeError, ValueError):
                row_count = None
    return upstream_ok, row_count


def _labels_for_end_client(
    ec: EndClient | None,
    *,
    project_company_id: int,
    client_id: int,
) -> tuple[str, str | None, str | None]:
    """
    Etiquetas de cliente final para el tablero Field.

    - Solo tratamos como cliente final una fila end_clients no borrada y con el mismo
      company_id que el proyecto (Alpha contrata Field; Pepsi es end_client de Alpha).
    - client_display_name: external_ref si existe, si no name (lo que Alpha usa como «clave»).
    """
    if ec is None or ec.deleted_at is not None or ec.company_id != project_company_id:
        suffix = f"#{client_id}"
        return (
            f"Cliente {suffix}",
            None,
            None,
        )
    name = (ec.name or "").strip()
    ref = (ec.external_ref or "").strip()
    display = ref if ref else name
    return (
        display or f"Cliente #{client_id}",
        name or None,
        ref or None,
    )


def _compute_health(
    *,
    ingest_mode: str,
    actionable_error: int,
    actionable_warn: int,
    pending_review: int,
    active_dooblo: int,
    dooblo_with_survey: int,
    last_analysis_status: str | None,
    last_sync_at: datetime | None,
    quota_upstream_ok: bool | None,
    completion_rate: float | None,
    sample_target: int | None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if last_analysis_status == "failed":
        reasons.append("Último análisis Dooblo terminó en fallo.")

    if ingest_mode == "dooblo":
        if active_dooblo > 0 and dooblo_with_survey == 0:
            reasons.append("Hay fuentes Dooblo activas pero falta ID de encuesta en el vínculo.")
        if _is_stale(last_sync_at, 7):
            reasons.append("Sin sincronización de ejecución reciente (más de 7 días o nunca).")

    if actionable_error > 0:
        reasons.append(f"{actionable_error} hallazgo(s) crítico(s) sin cerrar (error).")

    if quota_upstream_ok is False:
        reasons.append("Cuota en SurveyToGo: respuesta upstream no OK en último snapshot.")

    if completion_rate is not None and sample_target and sample_target > 0:
        if completion_rate < 0.85:
            reasons.append(
                f"Avance muestral bajo (~{completion_rate * 100:.0f}% vs objetivo declarado)."
            )

    if actionable_error > 0 or last_analysis_status == "failed":
        return "red", reasons

    if (
        actionable_warn > 0
        or pending_review > 0
        or quota_upstream_ok is False
        or (ingest_mode == "dooblo" and active_dooblo > 0 and dooblo_with_survey == 0)
        or (completion_rate is not None and sample_target and sample_target > 0 and completion_rate < 0.85)
        or (ingest_mode == "dooblo" and _is_stale(last_sync_at, 7))
    ):
        # Ámbar acumula también razones «suaves»
        if actionable_warn > 0:
            reasons.append(f"{actionable_warn} advertencia(s) operativa(s) abiertas.")
        if pending_review > 0:
            reasons.append(f"{pending_review} hallazgo(s) pendientes de revisión/aprobación.")
        return "amber", reasons

    return "green", reasons


async def _field_project_overview_rows(
    session: AsyncSession,
    projects: list[FieldProjectPublic],
) -> list[FieldProjectOverviewRow]:
    if not projects:
        return []

    ids = [p.id for p in projects]
    id_set = frozenset(ids)

    client_ids = {p.client_id for p in projects}
    study_ids = {p.study_id for p in projects if p.study_id}

    clients_res = await session.execute(
        select(EndClient).where(
            EndClient.id.in_(client_ids),
            EndClient.deleted_at.is_(None),
        )
    )
    client_by_id: dict[int, EndClient] = {
        int(c.id): c for c in clients_res.scalars().all() if c.id is not None
    }

    study_map: dict[int, str] = {}
    if study_ids:
        st_res = await session.execute(select(FieldStudy).where(FieldStudy.id.in_(study_ids)))
        study_map = {s.id: s.name for s in st_res.scalars().all()}

    # --- KPIs: último valor por metric_code y proyecto ---
    met_rows = (
        (
            await session.execute(
                select(FieldMetric)
                .where(FieldMetric.field_project_id.in_(ids))
                .order_by(FieldMetric.field_project_id, FieldMetric.calculated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    latest_metric_by_proj: dict[int, dict[str, FieldMetric]] = defaultdict(dict)
    for m in met_rows:
        bucket = latest_metric_by_proj[m.field_project_id]
        if m.metric_code not in bucket:
            bucket[m.metric_code] = m

    # --- Encuestas Field enlazadas ---
    sc_rows = (
        (
            await session.execute(
                select(FieldSurvey.field_project_id, func.count(FieldSurvey.id)).where(
                    FieldSurvey.field_project_id.in_(ids)
                ).group_by(FieldSurvey.field_project_id)
            )
        )
        .all()
    )
    survey_counts = {int(pid): int(c) for pid, c in sc_rows}

    # --- Fuentes Dooblo ---
    src_rows = (
        (
            await session.execute(
                select(FieldProjectExternalSource).where(
                    FieldProjectExternalSource.field_project_id.in_(ids),
                    FieldProjectExternalSource.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    dooblo_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"active": 0, "with_survey": 0})
    for s in src_rows:
        if s.source_type != SOURCE_TYPE_DOOBLO:
            continue
        pid = s.field_project_id
        dooblo_counts[pid]["active"] += 1
        if s.external_survey_id and str(s.external_survey_id).strip():
            dooblo_counts[pid]["with_survey"] += 1

    # --- Hallazgos accionables (no aprobados) ---
    actionable_where = or_(
        FieldFinding.approval_status.is_(None),
        FieldFinding.approval_status != "approved",
    )
    fb_rows = (
        (
            await session.execute(
                select(FieldFinding.field_project_id, FieldFinding.severity, func.count(FieldFinding.id))
                .where(
                    FieldFinding.field_project_id.in_(ids),
                    FieldFinding.severity.in_(("error", "warn", "info")),
                    actionable_where,
                )
                .group_by(FieldFinding.field_project_id, FieldFinding.severity)
            )
        )
        .all()
    )
    findings_open: dict[int, dict[str, int]] = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0})
    for pid, sev, cnt in fb_rows:
        if pid not in id_set:
            continue
        key = str(sev).lower()
        if key in findings_open[pid]:
            findings_open[pid][key] = int(cnt)

    pending_rows = (
        (
            await session.execute(
                select(FieldFinding.field_project_id, func.count(FieldFinding.id)).where(
                    FieldFinding.field_project_id.in_(ids),
                    FieldFinding.severity.in_(("error", "warn")),
                    or_(
                        FieldFinding.approval_status.is_(None),
                        FieldFinding.approval_status == "pending",
                    ),
                ).group_by(FieldFinding.field_project_id)
            )
        )
        .all()
    )
    pending_map = {int(pid): int(c) for pid, c in pending_rows}

    # --- Última corrida field_analysis por proyecto ---
    run_rows = (
        (
            await session.execute(
                select(FieldSyncRun).where(
                    FieldSyncRun.field_project_id.in_(ids),
                    FieldSyncRun.run_kind == RUN_KIND_FIELD_ANALYSIS,
                ).order_by(FieldSyncRun.field_project_id, FieldSyncRun.started_at.desc())
            )
        )
        .scalars()
        .all()
    )
    latest_analysis: dict[int, FieldSyncRun] = {}
    for r in run_rows:
        if r.field_project_id not in latest_analysis:
            latest_analysis[r.field_project_id] = r

    # --- Último import CSV por proyecto ---
    imp_rows = (
        (
            await session.execute(
                select(FieldImportRun).where(FieldImportRun.field_project_id.in_(ids)).order_by(
                    FieldImportRun.field_project_id,
                    FieldImportRun.created_at.desc(),
                )
            )
        )
        .scalars()
        .all()
    )
    latest_import: dict[int, FieldImportRun] = {}
    for r in imp_rows:
        if r.field_project_id not in latest_import:
            latest_import[r.field_project_id] = r

    # --- Snapshot operacional ---
    snap_rows = (
        (
            await session.execute(
                select(FieldOperationalSnapshot).where(
                    FieldOperationalSnapshot.field_project_id.in_(ids)
                )
            )
        )
        .scalars()
        .all()
    )
    snap_map = {s.field_project_id: s for s in snap_rows}

    out: list[FieldProjectOverviewRow] = []
    for proj in projects:
        pid = proj.id
        kpis_list = [
            FieldMetricPublic.model_validate(v)
            for _, v in sorted(latest_metric_by_proj.get(pid, {}).items())
        ]
        cr_metric = latest_metric_by_proj.get(pid, {}).get("completion_rate")
        completion_rate: float | None = None
        sample_target: int | None = None
        if cr_metric is not None:
            completion_rate = float(cr_metric.value)
            dims: dict[str, Any] = cr_metric.dimensions or {}
            try:
                sample_target = int(dims.get("sample_target", 0)) or None
            except (TypeError, ValueError):
                sample_target = None

        dc = dooblo_counts.get(pid, {"active": 0, "with_survey": 0})
        fo = findings_open.get(pid, {"error": 0, "warn": 0, "info": 0})

        analysis = latest_analysis.get(pid)
        imp = latest_import.get(pid)
        snap = snap_map.get(pid)
        q_ok, tab_rows = _quota_signals(snap)

        ingest = (proj.ingest_mode or "csv").strip().lower()
        actionable_error = int(fo["error"])
        actionable_warn = int(fo["warn"])
        pending_review = int(pending_map.get(pid, 0))

        health, reasons = _compute_health(
            ingest_mode=ingest,
            actionable_error=actionable_error,
            actionable_warn=actionable_warn,
            pending_review=pending_review,
            active_dooblo=int(dc["active"]),
            dooblo_with_survey=int(dc["with_survey"]),
            last_analysis_status=analysis.status if analysis else None,
            last_sync_at=proj.last_execution_sync_at,
            quota_upstream_ok=q_ok,
            completion_rate=completion_rate,
            sample_target=sample_target,
        )

        ec_row = client_by_id.get(proj.client_id)
        client_display_name, client_name, client_external_ref = _labels_for_end_client(
            ec_row,
            project_company_id=proj.company_id,
            client_id=proj.client_id,
        )

        out.append(
            FieldProjectOverviewRow(
                project=proj,
                client_display_name=client_display_name,
                client_name=client_name,
                client_external_ref=client_external_ref,
                study_display_name=study_map.get(proj.study_id) if proj.study_id else None,
                kpis_latest=kpis_list,
                findings_open_by_severity=dict(fo),
                findings_pending_review=pending_review,
                surveys_linked_count=int(survey_counts.get(pid, 0)),
                active_dooblo_sources=int(dc["active"]),
                dooblo_sources_with_survey_id=int(dc["with_survey"]),
                last_analysis_run_status=analysis.status if analysis else None,
                last_analysis_run_at=analysis.started_at if analysis else None,
                last_csv_import_status=imp.status if imp else None,
                last_csv_import_at=imp.created_at if imp else None,
                operational_snapshot_at=snap.last_calculated_at if snap else None,
                health=health,
                health_reasons=reasons,
                quota_upstream_ok=q_ok,
                tabular_row_count=tab_rows,
            )
        )

    # Orden: peor salud primero, luego más hallazgos error
    rank = {"red": 0, "amber": 1, "green": 2}

    def sort_key(row: FieldProjectOverviewRow) -> tuple[int, int, str]:
        fo = row.findings_open_by_severity
        err = int(fo.get("error", 0))
        return (rank.get(row.health, 9), -err, row.project.name.lower())

    out.sort(key=sort_key)
    return out


async def list_field_projects_overview(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    client_id: Optional[int],
) -> list[FieldProjectOverviewRow]:
    projects = await list_field_projects(session, user, company_id, client_id)
    return await _field_project_overview_rows(session, projects)


async def get_field_project_overview_drilldown(
    session: AsyncSession,
    user: User,
    project_id: int,
    top_findings_limit: int = 8,
) -> FieldProjectOverviewRow:
    """
    Clic 3 — salud del proyecto en una sola respuesta: mismos agregados que la fila del
    listado overview + muestra corta de hallazgos abiertos ordenados por severidad.
    """
    await assert_field_staff(user)
    proj_orm = await _get_field_project_writable(session, project_id)
    _assert_project_company_access(user, proj_orm)
    pub = FieldProjectPublic.model_validate(proj_orm)
    rows = await _field_project_overview_rows(session, [pub])
    row = rows[0]

    if top_findings_limit > 0:
        sev_order = case(
            (FieldFinding.severity == "error", 0),
            (FieldFinding.severity == "warn", 1),
            else_=2,
        )
        stmt = (
            select(FieldFinding)
            .where(
                FieldFinding.field_project_id == project_id,
                or_(
                    FieldFinding.approval_status.is_(None),
                    FieldFinding.approval_status != "approved",
                ),
            )
            .order_by(sev_order, FieldFinding.created_at.desc())
            .limit(top_findings_limit)
        )
        res = await session.execute(stmt)
        row.top_findings = [FieldFindingPublic.model_validate(f) for f in res.scalars().all()]
    return row
