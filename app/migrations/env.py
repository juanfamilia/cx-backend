import os
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

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def get_url():
    """Get database URL from environment variable, converting asyncpg to psycopg2 for sync operations."""
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise ValueError("POSTGRES_URI environment variable is not set")
    if "postgresql+asyncpg://" in postgres_uri:
        postgres_uri = postgres_uri.replace("postgresql+asyncpg://", "postgresql://")
    return postgres_uri

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (recommended)."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
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
    run_migrations_online()
