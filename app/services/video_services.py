from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video_model import Video
from app.utils.exeptions import NotFoundException


async def create_video(session: AsyncSession, url: str, title: str) -> Video:

    video = Video(url=url, title=title)

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
    """Return the video row. `videos.status` was removed in migration ddbcc7fdc927."""
    video = await get_video(session, video_id)
    return video
