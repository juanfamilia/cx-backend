from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    # Required settings
    PROJECT_NAME: str = "Siete CX"
    API_URL: str = "/api/v1"
    JWT_SECRET_KEY: str = "temp-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE: int = 1440
    POSTGRES_URI: str = "postgresql+asyncpg://localhost/db"
    
    # Optional settings (for staging/development)
    CLOUDFLARE_STREAM_KEY: Optional[str] = None
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET: Optional[str] = None
    R2_ENDPOINT_URL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    @field_validator('POSTGRES_URI')
    @classmethod
    def convert_postgres_uri_to_async(cls, v: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// for async support"""
        if v.startswith('postgresql://') and '+asyncpg' not in v:
            return v.replace('postgresql://', 'postgresql+asyncpg://')
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# For backwards compatibility
settings = get_settings()
