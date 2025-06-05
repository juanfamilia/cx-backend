import uuid
import boto3
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.video_model import Video
from app.utils.helpers.s3_get_url import get_s3_url

s3 = boto3.client("s3")


async def upload_raw_video(
    session: AsyncSession, media: UploadFile, title: str
) -> Video:
    ext = media.filename.split(".")[-1]
    video_id = str(uuid.uuid4())
    raw_key = f"raw/{video_id}.{ext}"
    compressed_key = f"compressed/{video_id}.{ext}"

    s3.upload_fileobj(media.file, settings.AWS_BUCKET_NAME, raw_key)

    # Save video to database
    video = await create_video(session, get_s3_url(compressed_key), title)

    return video


async def create_video(session: AsyncSession, url: str, title: str) -> Video:

    video = Video(url=url, title=title)

    session.add(video)
    await session.commit()
    await session.refresh(video)

    return video
