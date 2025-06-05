from fastapi import UploadFile
from uuid import uuid4

from app.core.config import settings


def get_s3_url(key: str):
    return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
