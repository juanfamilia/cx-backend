import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Import ALL DB models to ensure they're registered with SQLModel.metadata
from app.models import (
    User,
    Company,
    Campaign,
    Evaluation,
    EvaluationAnalysis,
    Zone,
    SurveySection,
    SurveyAspect,
    SurveyForm,
    Notification,
    Payment,
    DashboardConfig,
    Insight,
    Tag,
    EvaluationTag,
    AlertThreshold,
    Trend,
    PromptManager,
    Widget,
    Video,
    CampaignUser,
    CampaignZone,
    UserZone,
    OnboardingStatus,
    CampaignGoalsEvaluator,
    CampaignGoalsProgress,
    UserEvaluationSummary,
)

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def get_url():
    """Get database URL from environment variables, converting asyncpg to psycopg2 for sync operations."""
    postgres_uri = os.getenv("POSTGRES_URI") or os.getenv("DATABASE_URL")
    print("DEBUG POSTGRES_URI raw:", postgres_uri)
    if not postgres_uri:
        raise ValueError("POSTGRES_URI or DATABASE_URL environment variable is not set")
    postgres_uri = postgres_uri.strip().strip('"').strip("'")
    if "postgresql+asyncpg://" in postgres_uri:
        postgres_uri = postgres_uri.replace("postgresql+asyncpg://", "postgresql://")
    print("DEBUG POSTGRES_URI final:", postgres_uri)
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
