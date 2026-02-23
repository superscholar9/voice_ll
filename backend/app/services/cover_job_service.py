"""Service helpers for cover job persistence."""

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoverJob


async def create_cover_job(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    input_voice_path: str,
    input_song_path: str,
    model_id: Optional[str] = None,
    pitch_shift: int = 0,
) -> CoverJob:
    """Create and persist a new cover job."""
    job = CoverJob(
        id=job_id,
        user_id=user_id,
        status="queued",
        stage="queued",
        progress=0,
        model_id=model_id,
        pitch_shift=pitch_shift,
        input_voice_path=input_voice_path,
        input_song_path=input_song_path,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_cover_job(session: AsyncSession, job_id: uuid.UUID) -> Optional[CoverJob]:
    """Get a cover job by its identifier."""
    result = await session.execute(select(CoverJob).where(CoverJob.id == job_id))
    return result.scalar_one_or_none()


async def update_cover_job(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    progress: Optional[int] = None,
    task_id: Optional[str] = None,
    output_vocal_path: Optional[str] = None,
    output_inst_path: Optional[str] = None,
    output_mix_path: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[CoverJob]:
    """Update mutable fields on a cover job."""
    job = await get_cover_job(session, job_id)
    if job is None:
        return None

    if status is not None:
        job.status = status
    if stage is not None:
        job.stage = stage
    if progress is not None:
        job.progress = max(0, min(100, int(progress)))
    if task_id is not None:
        job.task_id = task_id
    if output_vocal_path is not None:
        job.output_vocal_path = output_vocal_path
    if output_inst_path is not None:
        job.output_inst_path = output_inst_path
    if output_mix_path is not None:
        job.output_mix_path = output_mix_path
    if error_message is not None:
        job.error_message = error_message

    await session.commit()
    await session.refresh(job)
    return job
