"""
Clip Generation Service
Extracts video clips from evaluations based on GPT-detected verbatims
"""
import asyncio
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx
from moviepy import VideoFileClip
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from shared.core.config import settings
from shared.models.clip_model import (
    Clip, 
    ClipConfig, 
    ClipCreate, 
    ClipStatus, 
    ClipUpdate,
    VerbatimType
)
from shared.models.evaluation_model import Evaluation
from shared.models.evaluation_analysis_model import EvaluationAnalysis
from shared.models.campaign_model import Campaign
from shared.services.cloudflare_stream_services import (
    get_download_status,
    wait_until_ready_to_stream,
    enable_download,
)


# ============ DEFAULT CONFIGURATION ============

@dataclass
class ClipDurationConfig:
    """Duration configuration for a verbatim type"""
    before: int  # seconds before timestamp
    after: int   # seconds after timestamp


DEFAULT_CLIP_CONFIGS = {
    VerbatimType.CRITICAL: ClipDurationConfig(before=10, after=20),
    VerbatimType.NEGATIVE: ClipDurationConfig(before=5, after=15),
    VerbatimType.POSITIVE: ClipDurationConfig(before=5, after=10),
}

MAX_CLIP_DURATION = 60  # seconds
MAX_CLIPS_DELIVERED = 5


# ============ HELPER FUNCTIONS ============

def parse_timestamp_to_seconds(timestamp: str) -> int:
    """
    Convert mm:ss or hh:mm:ss format to seconds
    
    Args:
        timestamp: Time string like "02:34" or "1:02:34"
    
    Returns:
        Total seconds
    """
    parts = timestamp.strip().split(":")
    
    if len(parts) == 2:
        # mm:ss
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # hh:mm:ss
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def calculate_priority_score(
    verbatim_type: VerbatimType,
    metrics: dict | None = None
) -> float:
    """
    Calculate priority score for a clip
    
    Scoring logic:
    - Critical verbatims start at 100
    - Negative verbatims start at 50
    - Positive verbatims start at 10
    - IRD score adds up to 30 points
    - CES score adds up to 20 points
    """
    base_scores = {
        VerbatimType.CRITICAL: 100.0,
        VerbatimType.NEGATIVE: 50.0,
        VerbatimType.POSITIVE: 10.0,
    }
    
    score = base_scores.get(verbatim_type, 0.0)
    
    if metrics:
        # Add IRD contribution (higher IRD = higher priority)
        ird = metrics.get("IRD", {}).get("score", 0)
        score += (ird / 100) * 30  # Max 30 points from IRD
        
        # Add CES contribution (higher CES = more effort = higher priority)
        ces = metrics.get("CES", {}).get("score", 0)
        score += (ces / 100) * 20  # Max 20 points from CES
    
    return round(score, 2)


def parse_verbatims_from_analysis(analysis: EvaluationAnalysis) -> list[dict]:
    """
    Extract verbatims from the operative view JSON
    
    Returns list of dicts with:
    - type: critical/negative/positive
    - text: verbatim text
    - timestamp: original timestamp string
    - origin: cliente/colaborador
    """
    verbatims = []
    
    if not analysis.operative_view:
        print("⚠️ No operative_view in analysis")
        return verbatims
    
    try:
        # Try to parse as JSON
        operative_data = json.loads(analysis.operative_view)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```json\s*(.*?)\s*```', analysis.operative_view, re.DOTALL)
        if json_match:
            try:
                operative_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                print("⚠️ Could not parse JSON from operative_view")
                return verbatims
        else:
            print("⚠️ No JSON found in operative_view")
            return verbatims
    
    # Extract Verbatims section
    verbatims_data = operative_data.get("Verbatims", {})
    
    # Process each type
    for verbatim_type, type_enum in [
        ("criticos", VerbatimType.CRITICAL),
        ("negativos", VerbatimType.NEGATIVE),
        ("positivos", VerbatimType.POSITIVE),
    ]:
        items = verbatims_data.get(verbatim_type, [])
        for item in items:
            if isinstance(item, dict) and "timestamp" in item:
                verbatims.append({
                    "type": type_enum,
                    "text": item.get("texto", item.get("text", "")),
                    "timestamp": item.get("timestamp", "00:00"),
                    "origin": item.get("origen", item.get("origin", "cliente")),
                })
    
    return verbatims


# ============ CLIP CONFIGURATION SERVICE ============

async def get_clip_config(session: AsyncSession, company_id: int) -> ClipConfig | None:
    """Get clip configuration for a company"""
    query = select(ClipConfig).where(
        ClipConfig.company_id == company_id,
        ClipConfig.is_active == True
    )
    result = await session.execute(query)
    return result.scalars().first()


async def get_or_create_default_config(
    session: AsyncSession, 
    company_id: int
) -> tuple[ClipDurationConfig, ClipDurationConfig, ClipDurationConfig, int, int]:
    """
    Get config for company or return defaults
    
    Returns tuple of:
    - critical_config
    - negative_config  
    - positive_config
    - max_duration
    - max_delivered
    """
    config = await get_clip_config(session, company_id)
    
    if config:
        return (
            ClipDurationConfig(before=config.critical_before, after=config.critical_after),
            ClipDurationConfig(before=config.negative_before, after=config.negative_after),
            ClipDurationConfig(before=config.positive_before, after=config.positive_after),
            config.max_clip_duration,
            config.max_clips_delivered,
        )
    
    # Return defaults
    return (
        DEFAULT_CLIP_CONFIGS[VerbatimType.CRITICAL],
        DEFAULT_CLIP_CONFIGS[VerbatimType.NEGATIVE],
        DEFAULT_CLIP_CONFIGS[VerbatimType.POSITIVE],
        MAX_CLIP_DURATION,
        MAX_CLIPS_DELIVERED,
    )


# ============ VIDEO PROCESSING ============

async def download_video_for_clipping(video_uid: str, dest_path: str) -> bool:
    """
    Download video from Cloudflare for clip extraction
    
    Returns True if successful
    """
    try:
        # Wait for video to be ready
        is_ready = await wait_until_ready_to_stream(video_uid, max_retries=5)
        if not is_ready:
            print(f"❌ Video {video_uid} not ready for download")
            return False
        
        # Enable download
        await enable_download(video_uid)
        
        # Wait for download URL
        for attempt in range(10):
            status, url = await get_download_status(video_uid)
            if status == "ready" and url:
                # Download video
                async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        with open(dest_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                print(f"✅ Video downloaded to {dest_path}")
                return True
            
            await asyncio.sleep(5)
        
        print(f"❌ Timeout waiting for download URL")
        return False
        
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return False


def extract_clip_from_video(
    video_path: str,
    output_path: str,
    start_seconds: int,
    end_seconds: int,
    video_duration: float
) -> bool:
    """
    Extract a clip from video file using moviepy
    
    Returns True if successful
    """
    try:
        # Clamp to video bounds
        start = max(0, start_seconds)
        end = min(end_seconds, int(video_duration))
        
        if start >= end:
            print(f"⚠️ Invalid clip range: {start}-{end}")
            return False
        
        with VideoFileClip(video_path) as video:
            clip = video.subclipped(start, end)
            clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=f"{output_path}_temp_audio.m4a",
                remove_temp=True,
                logger=None  # Suppress moviepy output
            )
        
        print(f"✅ Clip extracted: {start}s - {end}s")
        return True
        
    except Exception as e:
        print(f"❌ Error extracting clip: {e}")
        return False


async def upload_clip_to_cloudflare(clip_path: str, title: str) -> tuple[str | None, str | None]:
    """
    Upload a clip to Cloudflare Stream
    
    Returns tuple of (cloudflare_uid, stream_url) or (None, None) on failure
    """
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream"
        headers = {
            "Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_KEY}",
        }
        
        with open(clip_path, "rb") as f:
            files = {"file": (os.path.basename(clip_path), f, "video/mp4")}
            data = {"meta": json.dumps({"name": title})}
            
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                result = response.json().get("result", {})
                uid = result.get("uid")
                
                if uid:
                    stream_url = f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{uid}/manifest/video.m3u8"
                    print(f"✅ Clip uploaded to Cloudflare: {uid}")
                    return uid, stream_url
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error uploading clip to Cloudflare: {e}")
        return None, None


# ============ MAIN CLIP GENERATION SERVICE ============

async def generate_clips_for_evaluation(
    session: AsyncSession,
    evaluation_id: int,
    analysis: EvaluationAnalysis,
    video_uid: str,
    company_id: int
) -> list[Clip]:
    """
    Main function to generate clips for an evaluation
    
    Flow:
    1. Parse verbatims from analysis
    2. Calculate clip boundaries for each
    3. Download source video
    4. Extract each clip
    5. Upload to Cloudflare
    6. Save to database with priority scores
    7. Mark top N as delivered
    
    Returns list of created Clip objects
    """
    print(f"🎬 Starting clip generation for evaluation {evaluation_id}")
    
    # 1. Parse verbatims
    verbatims = parse_verbatims_from_analysis(analysis)
    if not verbatims:
        print("⚠️ No verbatims found in analysis")
        return []
    
    print(f"📝 Found {len(verbatims)} verbatims to process")
    
    # 2. Get configuration
    critical_cfg, negative_cfg, positive_cfg, max_duration, max_delivered = \
        await get_or_create_default_config(session, company_id)
    
    config_map = {
        VerbatimType.CRITICAL: critical_cfg,
        VerbatimType.NEGATIVE: negative_cfg,
        VerbatimType.POSITIVE: positive_cfg,
    }
    
    # 3. Extract metrics for priority calculation
    metrics = None
    if analysis.operative_view:
        try:
            metrics = json.loads(analysis.operative_view)
        except:
            pass
    
    # 4. Prepare clips data
    clips_to_create = []
    for v in verbatims:
        try:
            timestamp_sec = parse_timestamp_to_seconds(v["timestamp"])
            cfg = config_map[v["type"]]
            
            # Calculate boundaries
            start = max(0, timestamp_sec - cfg.before)
            end = timestamp_sec + cfg.after
            duration = end - start
            
            # Enforce max duration
            if duration > max_duration:
                # Trim from the end
                end = start + max_duration
                duration = max_duration
            
            priority = calculate_priority_score(v["type"], metrics)
            
            clips_to_create.append(ClipCreate(
                evaluation_id=evaluation_id,
                verbatim_type=v["type"],
                verbatim_text=v["text"],
                verbatim_origin=v["origin"],
                original_timestamp=timestamp_sec,
                clip_start=start,
                clip_end=end,
                clip_duration=duration,
                priority_score=priority,
                extra_data={"metrics_at_generation": metrics} if metrics else None
            ))
        except Exception as e:
            print(f"⚠️ Error processing verbatim: {e}")
            continue
    
    if not clips_to_create:
        print("⚠️ No valid clips to create")
        return []
    
    # 5. Create clip records in DB with PENDING status
    created_clips = []
    for clip_data in clips_to_create:
        db_clip = Clip(
            **clip_data.model_dump(),
            status=ClipStatus.PENDING
        )
        session.add(db_clip)
        created_clips.append(db_clip)
    
    await session.commit()
    for clip in created_clips:
        await session.refresh(clip)
    
    print(f"💾 Created {len(created_clips)} clip records in DB")
    
    # 6. Download source video
    tmp_dir = tempfile.gettempdir()
    video_path = f"{tmp_dir}/source_{evaluation_id}_{uuid.uuid4()}.mp4"
    
    download_success = await download_video_for_clipping(video_uid, video_path)
    if not download_success:
        # Mark all clips as failed
        for clip in created_clips:
            clip.status = ClipStatus.FAILED
            clip.error_message = "Failed to download source video"
        await session.commit()
        return created_clips
    
    # 7. Get video duration
    try:
        with VideoFileClip(video_path) as video:
            video_duration = video.duration
        print(f"📹 Video duration: {video_duration}s")
    except Exception as e:
        print(f"❌ Error reading video: {e}")
        for clip in created_clips:
            clip.status = ClipStatus.FAILED
            clip.error_message = f"Failed to read video: {e}"
        await session.commit()
        return created_clips
    
    # 8. Process each clip
    for clip in created_clips:
        clip.status = ClipStatus.PROCESSING
        await session.commit()
        
        clip_path = f"{tmp_dir}/clip_{clip.id}_{uuid.uuid4()}.mp4"
        
        try:
            # Extract clip
            success = await run_in_threadpool(
                extract_clip_from_video,
                video_path,
                clip_path,
                clip.clip_start,
                clip.clip_end,
                video_duration
            )
            
            if not success:
                clip.status = ClipStatus.FAILED
                clip.error_message = "Failed to extract clip"
                await session.commit()
                continue
            
            # Upload to Cloudflare
            clip.status = ClipStatus.UPLOADING
            await session.commit()
            
            title = f"Clip_{evaluation_id}_{clip.verbatim_type.value}_{clip.id}"
            cf_uid, stream_url = await upload_clip_to_cloudflare(clip_path, title)
            
            if cf_uid:
                clip.cloudflare_uid = cf_uid
                clip.stream_url = stream_url
                clip.thumbnail_url = f"https://customer-hmba8ctlrczwxylv.cloudflarestream.com/{cf_uid}/thumbnails/thumbnail.jpg"
                clip.status = ClipStatus.READY
            else:
                clip.status = ClipStatus.FAILED
                clip.error_message = "Failed to upload to Cloudflare"
            
            await session.commit()
            
        except Exception as e:
            clip.status = ClipStatus.FAILED
            clip.error_message = str(e)
            await session.commit()
        
        finally:
            # Clean up clip file
            if os.path.exists(clip_path):
                os.remove(clip_path)
    
    # 9. Clean up source video
    if os.path.exists(video_path):
        os.remove(video_path)
        print(f"🗑️ Cleaned up source video")
    
    # 10. Rank and mark delivered clips
    ready_clips = [c for c in created_clips if c.status == ClipStatus.READY]
    ready_clips.sort(key=lambda x: x.priority_score, reverse=True)
    
    for rank, clip in enumerate(ready_clips, start=1):
        clip.priority_rank = rank
        clip.is_delivered = rank <= max_delivered
    
    await session.commit()
    
    delivered_count = sum(1 for c in ready_clips if c.is_delivered)
    print(f"✅ Clip generation complete: {len(ready_clips)} ready, {delivered_count} delivered")
    
    return created_clips


# ============ CLIP QUERY SERVICES ============

async def get_clips_for_evaluation(
    session: AsyncSession,
    evaluation_id: int,
    delivered_only: bool = False
) -> list[Clip]:
    """Get clips for an evaluation"""
    query = select(Clip).where(
        Clip.evaluation_id == evaluation_id,
        Clip.deleted_at.is_(None),
        Clip.status == ClipStatus.READY
    )
    
    if delivered_only:
        query = query.where(Clip.is_delivered == True)
    
    query = query.order_by(Clip.priority_rank)
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_clip_by_id(session: AsyncSession, clip_id: int) -> Clip | None:
    """Get a single clip by ID"""
    query = select(Clip).where(
        Clip.id == clip_id,
        Clip.deleted_at.is_(None)
    )
    result = await session.execute(query)
    return result.scalars().first()
