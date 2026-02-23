"""Celery tasks for AI cover jobs."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import uuid

from app.db.session import async_session_maker
from app.services.cover_job_service import get_cover_job, update_cover_job
from app.services.cover_pipeline import CoverPipeline
from app.services.history_service import record_history
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _update_job(job_id: uuid.UUID, **kwargs) -> None:
    async with async_session_maker() as session:
        await update_cover_job(session, job_id=job_id, **kwargs)


async def _get_job(job_id: uuid.UUID):
    async with async_session_maker() as session:
        return await get_cover_job(session, job_id)


async def _record_cover_history(
    *,
    user_id,
    status: str,
    error_message: str | None = None,
) -> None:
    async with async_session_maker() as session:
        await record_history(
            session=session,
            user_id=user_id,
            job_type="cover",
            status=status,
            input_text="[cover_job]",
            language="auto",
            speed=1.0,
            temperature=1.0,
            duration_seconds=None,
            error_message=error_message,
        )


@celery_app.task(bind=True, name="cover.run_cover_job")
def run_cover_job(self, job_id: str) -> dict:
    """Run the full cover generation pipeline for a job id."""
    job_uuid = uuid.UUID(job_id)
    job = asyncio.run(_get_job(job_uuid))
    if job is None:
        raise RuntimeError(f"cover job not found: {job_id}")

    if job.status == "canceled":
        return {"job_id": job_id, "status": "canceled"}

    def report(stage: str, progress: int) -> None:
        asyncio.run(_update_job(job_uuid, status="running", stage=stage, progress=progress))

    try:
        report("preprocess", 5)

        pipeline = CoverPipeline()
        job_root = Path(job.input_song_path).resolve().parents[1]
        result = pipeline.run(
            work_root=job_root,
            reference_voice=Path(job.input_voice_path),
            song_input=Path(job.input_song_path),
            model_id=job.model_id or "default",
            pitch_shift=job.pitch_shift,
            progress_callback=report,
        )

        asyncio.run(
            _update_job(
                job_uuid,
                status="succeeded",
                stage="finalize",
                progress=100,
                output_vocal_path=str(result.vocal_path),
                output_inst_path=str(result.inst_path),
                output_mix_path=str(result.mix_path),
                error_message=None,
            )
        )
        asyncio.run(_record_cover_history(user_id=job.user_id, status="success"))
        return {"job_id": job_id, "status": "succeeded", "output": str(result.mix_path)}
    except Exception as exc:
        logger.exception("cover pipeline failed for job_id=%s", job_id)
        msg = str(exc)
        asyncio.run(_update_job(job_uuid, status="failed", stage="finalize", progress=100, error_message=msg))
        asyncio.run(_record_cover_history(user_id=job.user_id, status="error", error_message=msg))
        raise
