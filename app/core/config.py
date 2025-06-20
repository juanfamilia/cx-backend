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
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_REGION: str
    CLOUDFLARE_STREAM_KEY: str
    CLOUDFLARE_ACCOUNT_ID: str
    WEB_HOOK_URL: str
    SYMBL_APP_ID: str
    SYMBL_APP_SECRET: str


settings = Settings()
