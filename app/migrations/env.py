### Archivo 2: `env.py` - CORRECCIÓN COMPLETA
Action: file_editor str_replace /app/cx-backend/app/migrations/env.py --old-str "import asyncio
from logging.config import fileConfig
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from sqlmodel import SQLModel
from app.core.db import engine

from app.models import (
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
    campaign_goals_evaluator_model,
)

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def do_run_migrations(connection: Connection):
    \"\"\"Ejecuta las migraciones en un contexto síncrono.\"\"\"
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    \"\"\"Ejecuta las migraciones en modo asíncrono si se usa asyncpg.\"\"\"
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
        url=config.get_main_option(\"sqlalchemy.url\"), target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()" --new-str "import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Import ALL models to ensure they're registered with SQLModel.metadata
from app.models import (
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
    campaign_goals_evaluator_model,
    dashboard_config_model,
    intelligence_model,
    prompt_manager_model,
    theme_model,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = SQLModel.metadata


def get_url():
    \"\"\"Get database URL from environment variable, converting asyncpg to psycopg2 for sync operations.\"\"\"
    postgres_uri = os.getenv(\"POSTGRES_URI\")
    if not postgres_uri:
        raise ValueError(\"POSTGRES_URI environment variable is not set\")
    
    # Convert async driver to sync driver for Alembic
    if \"postgresql+asyncpg://\" in postgres_uri:
        postgres_uri = postgres_uri.replace(\"postgresql+asyncpg://\", \"postgresql://\")
    
    return postgres_uri


def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    \"\"\"
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={\"paramstyle\": \"named\"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    We use SYNCHRONOUS engine with psycopg2 (not asyncpg) for Alembic migrations.
    \"\"\"
    # Override sqlalchemy.url with environment variable
    configuration = config.get_section(config.config_ini_section)
    configuration[\"sqlalchemy.url\"] = get_url()
    
    # Create synchronous engine for migrations
    connectable = engine_from_config(
        configuration,
        prefix=\"sqlalchemy.\",
        poolclass=pool.NullPool,  # Don't pool connections for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()"
Observation: Edit was successful.
