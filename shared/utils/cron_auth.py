from fastapi import Header, HTTPException, status
from shared.core.config import settings


def verify_cron_secret(x_cron_secret: str = Header(...)):
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret",
        )
