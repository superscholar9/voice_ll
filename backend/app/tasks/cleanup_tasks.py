"""Celery tasks for cleaning up expired cover assets."""

from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import uuid

from sqlalchemy import select

from app.core.config import settings
from app.db.models.cover_job import CoverJob
from app.db.session import async_session_maker
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _get_expired_jobs(ttl_hours: int) -> List[CoverJob]:
    """Get jobs that are completed/failed/canceled and older than TTL."""
    cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)

    async with async_session_maker() as session:
        stmt = select(CoverJob).where(
            CoverJob.status.in_(["succeeded", "failed", "canceled"]),
            CoverJob.created_at < cutoff_time
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def _get_all_job_ids() -> set[uuid.UUID]:
    """Get all job IDs from the database."""
    async with async_session_maker() as session:
        stmt = select(CoverJob.id)
        result = await session.execute(stmt)
        return set(result.scalars().all())


def cleanup_expired_assets(ttl_hours: int | None = None, dry_run: bool = False) -> dict:
    """
    Clean up expired cover asset directories.

    Args:
        ttl_hours: Time-to-live in hours. Defaults to COVER_RESULT_TTL_HOURS from settings.
        dry_run: If True, only log what would be deleted without actually deleting.

    Returns:
        Dictionary with cleanup statistics.
    """
    if ttl_hours is None:
        ttl_hours = settings.COVER_RESULT_TTL_HOURS

    cover_root = Path(settings.COVER_ASSET_ROOT)

    if not cover_root.exists():
        logger.info("Cover assets directory does not exist: %s", cover_root)
        return {"deleted_count": 0, "freed_bytes": 0, "orphaned_count": 0}

    deleted_count = 0
    orphaned_count = 0
    freed_bytes = 0

    # Get expired jobs from database
    expired_jobs = asyncio.run(_get_expired_jobs(ttl_hours))
    expired_job_ids = {job.id for job in expired_jobs}

    # Get all job IDs for orphan detection
    all_job_ids = asyncio.run(_get_all_job_ids())

    cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)

    # Scan cover_assets directory
    if not cover_root.is_dir():
        logger.warning("Cover assets path is not a directory: %s", cover_root)
        return {"deleted_count": 0, "freed_bytes": 0, "orphaned_count": 0}

    for job_dir in cover_root.iterdir():
        if not job_dir.is_dir():
            continue

        try:
            job_id = uuid.UUID(job_dir.name)
        except ValueError:
            logger.warning("Invalid job directory name (not a UUID): %s", job_dir.name)
            continue

        # Check if this is an expired job
        if job_id in expired_job_ids:
            dir_size = sum(f.stat().st_size for f in job_dir.rglob('*') if f.is_file())

            if dry_run:
                logger.info("[DRY RUN] Would delete expired job directory: %s (%.2f MB)",
                           job_dir, dir_size / (1024 * 1024))
            else:
                logger.info("Deleting expired job directory: %s (%.2f MB)",
                           job_dir, dir_size / (1024 * 1024))
                shutil.rmtree(job_dir)
                freed_bytes += dir_size

            deleted_count += 1

        # Check if this is an orphaned directory (no DB record)
        elif job_id not in all_job_ids:
            # Check directory age
            dir_mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
            if dir_mtime < cutoff_time:
                dir_size = sum(f.stat().st_size for f in job_dir.rglob('*') if f.is_file())

                if dry_run:
                    logger.info("[DRY RUN] Would delete orphaned directory: %s (%.2f MB)",
                               job_dir, dir_size / (1024 * 1024))
                else:
                    logger.info("Deleting orphaned directory: %s (%.2f MB)",
                               job_dir, dir_size / (1024 * 1024))
                    shutil.rmtree(job_dir)
                    freed_bytes += dir_size

                orphaned_count += 1

    logger.info("Cleanup complete: deleted=%d, orphaned=%d, freed=%.2f MB",
               deleted_count, orphaned_count, freed_bytes / (1024 * 1024))

    return {
        "deleted_count": deleted_count,
        "orphaned_count": orphaned_count,
        "freed_bytes": freed_bytes,
    }


@celery_app.task(name="cover.cleanup_expired_assets")
def cleanup_expired_assets_task() -> dict:
    """Celery periodic task to clean up expired cover assets."""
    logger.info("Starting scheduled cleanup of expired cover assets")
    return cleanup_expired_assets()
