"""Catálogo Framework Library PRE-FIELD (plantillas metodológicas versionadas).

Revision ID: z1y2x3w4v5u6
Revises: r8n7s6r5q4p3
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "z1y2x3w4v5u6"
down_revision: Union[str, None] = "r8n7s6r5q4p3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_framework_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("study_type", sa.String(length=64), nullable=False),
        sa.Column("framework_version", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "coverage_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("stub_spec_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_field_framework_templates_slug_version",
        "field_framework_templates",
        ["slug", "framework_version"],
        unique=True,
    )
    op.create_index(
        "ix_field_framework_templates_study_type_active",
        "field_framework_templates",
        ["study_type", "is_active"],
        unique=False,
    )

    # Seed inicial (catálogo global; multi-tenant por empresa — backlog)
    rules_cx = {
        "required_section_kinds": ["main"],
        "recommended_measurement_threads": [
            "recent_experience",
            "touchpoint",
            "satisfaction",
            "friction",
            "recommendation_intent",
        ],
        "qa_hints": [
            "Incluir bloque explícito de screening o cuotas si el brief lo exige.",
            "Evitar doble varilla en ítems de satisfacción y NPS/ recomendación.",
        ],
    }
    stub_cx = {
        "instrument_spec_version": "2026.1-draft",
        "study_type": "cx",
        "title": "CX — plantilla base",
        "blocks": [
            {
                "block_id": "SCR",
                "title": "Screening",
                "section_kind": "screener",
                "items": [],
            },
            {
                "block_id": "CX_MAIN",
                "title": "Experiencia y satisfacción",
                "section_kind": "main",
                "items": [],
            },
            {
                "block_id": "DEMO",
                "title": "Demográficos",
                "section_kind": "demographics",
                "items": [],
            },
        ],
    }

    rules_ua = {
        "required_section_kinds": ["main"],
        "recommended_measurement_threads": [
            "category_usage",
            "brand_health",
            "drivers_barriers",
            "purchase_intent",
        ],
    }
    stub_ua = {
        "instrument_spec_version": "2026.1-draft",
        "study_type": "ua",
        "title": "U&A — plantilla base",
        "blocks": [
            {"block_id": "SCR", "title": "Screening", "section_kind": "screener", "items": []},
            {"block_id": "UA_MAIN", "title": "Uso y actitud", "section_kind": "main", "items": []},
            {"block_id": "DEMO", "title": "Demográficos", "section_kind": "demographics", "items": []},
        ],
    }

    rules_bt = {
        "required_section_kinds": ["main"],
        "recommended_measurement_threads": [
            "awareness",
            "consideration",
            "preference",
            "imagery",
        ],
    }
    stub_bt = {
        "instrument_spec_version": "2026.1-draft",
        "study_type": "brand_tracking",
        "title": "Brand tracking — plantilla base",
        "blocks": [
            {"block_id": "SCR", "title": "Screening", "section_kind": "screener", "items": []},
            {"block_id": "BT_MAIN", "title": "Marca y competencia", "section_kind": "main", "items": []},
            {"block_id": "DEMO", "title": "Demográficos", "section_kind": "demographics", "items": []},
        ],
    }

    templates = sa.table(
        "field_framework_templates",
        sa.column("slug", sa.String),
        sa.column("study_type", sa.String),
        sa.column("framework_version", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("coverage_rules", postgresql.JSONB),
        sa.column("stub_spec_json", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        templates,
        [
            {
                "slug": "cx_core_v1",
                "study_type": "cx",
                "framework_version": "2026.1",
                "title": "CX — núcleo (experiencia / touchpoints / fricción)",
                "description": "Estructura sugerida para estudios CX cuantitativos con screening, bloque principal y demográficos.",
                "coverage_rules": rules_cx,
                "stub_spec_json": stub_cx,
                "sort_order": 10,
                "is_active": True,
            },
            {
                "slug": "ua_core_v1",
                "study_type": "ua",
                "framework_version": "2026.1",
                "title": "U&A — uso y actitud",
                "description": "Esqueleto para categoría, barreras y drivers.",
                "coverage_rules": rules_ua,
                "stub_spec_json": stub_ua,
                "sort_order": 20,
                "is_active": True,
            },
            {
                "slug": "brand_tracking_core_v1",
                "study_type": "brand_tracking",
                "framework_version": "2026.1",
                "title": "Brand tracking — embudo marca",
                "description": "Consciencia, consideración e imagen básica.",
                "coverage_rules": rules_bt,
                "stub_spec_json": stub_bt,
                "sort_order": 30,
                "is_active": True,
            },
            {
                "slug": "generic_quant_v1",
                "study_type": "other",
                "framework_version": "2026.1",
                "title": "Cuantitativo genérico",
                "description": "Mínimo viable de secciones cuando el tipo de estudio aún no tiene plantilla dedicada.",
                "coverage_rules": {"required_section_kinds": ["main"], "recommended_measurement_threads": []},
                "stub_spec_json": {
                    "instrument_spec_version": "2026.1-draft",
                    "study_type": "other",
                    "title": "Estudio — borrador",
                    "blocks": [
                        {"block_id": "SCR", "title": "Screening", "section_kind": "screener", "items": []},
                        {"block_id": "MAIN", "title": "Contenido principal", "section_kind": "main", "items": []},
                        {"block_id": "DEMO", "title": "Demográficos", "section_kind": "demographics", "items": []},
                    ],
                },
                "sort_order": 100,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_field_framework_templates_study_type_active",
        table_name="field_framework_templates",
    )
    op.drop_index("uq_field_framework_templates_slug_version", table_name="field_framework_templates")
    op.drop_table("field_framework_templates")
