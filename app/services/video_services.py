import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from app.core.config import settings
from app.models.video_model import Video
from app.utils.exeptions import NotFoundException
from app.utils.helpers.s3_get_url import get_s3_url

s3 = boto3.client("s3")


async def upload_raw_video(
    session: AsyncSession, media: UploadFile, title: str
) -> Video:
    ext = media.filename.split(".")[-1]
    video_id = str(uuid.uuid4())
    raw_key = f"raw/{video_id}.{ext}"
    compressed_key = f"compressed/{video_id}.{ext}"

    async with aiofiles.open(media.filename, "wb") as f:
        while chunk := await media.read(1024 * 1024 * 4):  # Leer en bloques de 4MB
            await f.write(chunk)

    with open(media.filename, "rb") as file_obj:
        s3.upload_fileobj(file_obj, settings.AWS_BUCKET_NAME, raw_key)

    # Save video to database
    video = await create_video(session, get_s3_url(compressed_key), title)

    return video


async def create_video(session: AsyncSession, url: str, title: str) -> Video:

    video = Video(url=url, title=title, status="processing")

    session.add(video)
    await session.commit()
    await session.refresh(video)

    return video


async def get_video(session: AsyncSession, video_id: str) -> Video:

    video = await session.get(Video, video_id)

    if not video:
        raise NotFoundException("Video not found")

    return video


async def update_video_status(session: AsyncSession, video_id: int) -> Video:

    # Buscar el video en la base de datos
    video = await get_video(session, video_id)

    compressed_key = "/".join(video.url.split("/")[-2:])

    if not check_s3_object_exists(settings.AWS_BUCKET_NAME, compressed_key):
        return NotFoundException("Video processing")

    video.status = "available"
    await session.commit()
    await session.refresh(video)

    return video


def check_s3_object_exists(bucket_name: str, object_key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket_name, Key=object_key)
        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise False
