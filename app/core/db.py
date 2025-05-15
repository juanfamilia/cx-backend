from typing import AsyncGenerator
from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


engine = create_async_engine(
    settings.POSTGRES_URI,
    echo=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
