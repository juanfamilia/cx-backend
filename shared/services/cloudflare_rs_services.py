import boto3
from app.core.config import settings


def r2_upload(archivo_local, nombre_objetivo):
    session = boto3.Session()
    s3 = session.client(
        service_name="s3",
        region_name="enam",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        endpoint_url=settings.R2_ENDPOINT_URL,
    )
    with open(archivo_local, "rb") as data:
        s3.upload_fileobj(data, settings.R2_BUCKET, nombre_objetivo)
