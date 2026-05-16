"""Agregado ejecutivo por proyecto Field (tablero / centro de mando)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from app.models.field_execution_model import FieldMetricPublic
from app.models.field_ledger_model import FieldFindingPublic
from app.models.field_project_model import FieldProjectPublic
from app.study_intelligence.schemas import StudyIntelligenceBundlePublic


class FieldProjectOverviewRow(SQLModel):
    """Una fila del resumen multi-proyecto; métricas alineadas al ledger y ejecución."""

    model_config = ConfigDict(from_attributes=True)

    project: FieldProjectPublic
    # Cliente final (B2B2B): fila en end_clients bajo la misma empresa que el proyecto.
    # client_display_name prioriza external_ref (clave operativa de Alpha) y si no hay, name.
    client_display_name: str = ""
    client_name: str | None = Field(
        default=None,
        description="Nombre de cuenta / marca (end_clients.name) cuando el vínculo es válido.",
    )
    client_external_ref: str | None = Field(
        default=None,
        description="Clave o referencia externa del cliente final (end_clients.external_ref).",
    )
    study_display_name: str | None = None

    kpis_latest: list[FieldMetricPublic] = Field(default_factory=list)

    # Hallazgos accionables: severidad error/warn/info donde aún no está «approved».
    findings_open_by_severity: dict[str, int] = Field(default_factory=dict)
    findings_pending_review: int = 0

    surveys_linked_count: int = 0
    active_dooblo_sources: int = 0
    dooblo_sources_with_survey_id: int = 0
    active_qualtrics_sources: int = 0
    qualtrics_sources_with_survey_id: int = 0

    last_analysis_run_status: str | None = None
    last_analysis_run_at: datetime | None = None
    last_csv_import_status: str | None = None
    last_csv_import_at: datetime | None = None

    operational_snapshot_at: datetime | None = None

    # Semáforo ejecutivo: green | amber | red
    health: str = "green"
    health_reasons: list[str] = Field(default_factory=list)

    # Muestra corta para drill-down (clic 3); vacío en listado multi-proyecto.
    top_findings: list[FieldFindingPublic] = Field(default_factory=list)

    # Study Intelligence persistido (PRE-FIELD lineage): solo drill-down cuando hay `study_id` + snapshot.
    study_intelligence: StudyIntelligenceBundlePublic | None = None

    # Resumen compacto de snapshot (cuota / muestra tabular) para UI sin parsear JSON profundo
    quota_upstream_ok: bool | None = None
    tabular_row_count: int | None = None
