from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Busca .env en dos ubicaciones para soportar tanto el entorno local
    # (archivo .env en la raíz del proyecto) como el contenedor Docker
    # (docker-entrypoint.sh hace `cd /app` y el .env vive en `/` = `../.env`).
    # Si ambos existen, el segundo (../.env) tiene prioridad (comportamiento
    # preservado para producción).
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_ignore_empty=True,
        extra="ignore",
    )
    PROJECT_NAME: str
    PROJECT_MODE: str
    API_URL: str = "/api/v1"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE: int
    POSTGRES_URI: str
    CLOUDFLARE_STREAM_KEY: str
    CLOUDFLARE_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET: str
    R2_ENDPOINT_URL: str
    OPENAI_API_KEY: str
    # Hugging Face token para pyannote speaker diarization (opcional)
    HF_TOKEN: str | None = None
    # Orígenes adicionales para CORS (coma-separados, con o sin https://).
    # Ej. staging: https://tu-app-staging.vercel.app
    CORS_EXTRA_ORIGINS: str = ""
    # Opcional: regex de orígenes (p. ej. previews de Vercel). Requiere coincidencia completa con Origin.
    CORS_ORIGIN_REGEX: str | None = None

    # ── Email / SMTP (Hostinger) ─────────────────────────────────────────────
    SMTP_HOST: str = "smtp.hostinger.com"
    SMTP_PORT: int = 465          # 465 = SSL implícito; 587 = STARTTLS
    SMTP_USER: str | None = None  # ej. notificaciones@sieteic.com
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_NAME: str = "Siete CX"
    SMTP_ENABLED: bool = False    # poner True en prod una vez configurado SMTP_USER/PASSWORD


settings = Settings()
