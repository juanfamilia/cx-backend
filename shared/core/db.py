from typing import AsyncGenerator, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from shared.core.config import settings

# Variables globales para lazy loading
_engine: Optional[AsyncEngine] = None
_session_maker: Optional[sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Lazy loading del engine - solo se crea cuando se necesita"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.POSTGRES_URI,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker() -> sessionmaker:
    """Lazy loading del session maker"""
    global _session_maker
    if _session_maker is None:
        _session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para FastAPI - obtiene una sesión de DB"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session
