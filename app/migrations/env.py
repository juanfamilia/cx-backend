import asyncio
from logging.config import fileConfig

from alembic import context
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel


class _AlembicDbSettings(BaseSettings):
    """
    Solo `POSTGRES_URI` para migraciones: evita cargar `app.core.config.Settings`
    (JWT, R2, OpenAI, etc.) al ejecutar `alembic upgrade`.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_ignore_empty=True,
        extra="ignore",
    )
    POSTGRES_URI: str


def _async_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


_db = _AlembicDbSettings()
engine = create_async_engine(
    _async_database_url(_db.POSTGRES_URI),
    echo=False,
)

from app.models import (  # noqa: E402 — tras definir `engine` (metadata)
    user_model,
    company_model,
    payment_model,
    zone_model,
    user_zone_model,
    video_model,
    survey_model,
    survey_forms_model,
    campaign_model,
    campaign_user_model,
    campaign_zone_model,
    evaluation_model,
    notification_model,
    evaluation_analysis_model,
    evaluation_event_model,
    transcript_segment_model,
    campaign_goals_evaluator_model,
    prompt_model,
    insight_model,
    clip_model,
    industry_model,
    framework_model,
    quality_competency_model,
    industry_template_model,
    company_competency_config_model,
    ins_study_model,
    end_client_model,
    field_project_model,
    field_decision_model,
    field_ledger_model,
    company_dooblo_model,
)

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def do_run_migrations(connection: Connection):
    """Ejecuta las migraciones en un contexto síncrono."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Ejecuta las migraciones en modo asíncrono si se usa asyncpg."""
    connectable = engine

    if isinstance(connectable, AsyncEngine):

        async def async_migrations():
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

        asyncio.run(async_migrations())
    else:
        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
