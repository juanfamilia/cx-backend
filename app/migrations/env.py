import asyncio
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
