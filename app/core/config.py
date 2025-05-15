from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    PROJECT_NAME: str
    API_URL: str = "/api/v1"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE: int
    POSTGRES_URI: str


settings = Settings()
