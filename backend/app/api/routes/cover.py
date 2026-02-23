"""AI cover generation API routes."""

from __future__ import annotations

import logging
from pathlib import Path
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_optional
from app.core.config import settings
from app.core.security import verify_api_key
from app.db.models import User
from app.db.session import get_async_session
from app.models.schemas import (
    CoverCancelResponse,
    CoverCreateResponse,
    CoverJobStageEnum,
    CoverJobStatusEnum,
    CoverJobStatusResponse,
    ErrorResponse,
)
from app.services.cover_job_service import create_cover_job, get_cover_job, update_cover_job
from app.tasks.celery_app import celery_app
from app.tasks.cover_tasks import run_cover_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cover", tags=["cover"])


def _job_base_dir(job_id: uuid.UUID) -> Path:
    return Path(settings.COVER_ASSET_ROOT).resolve() / str(job_id)


def _validate_audio_upload(file: UploadFile) -> None:
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Expected audio/*.",
        )
    suffix = Path(file.filename or "").suffix.lower().lstrip(".")
    if suffix and suffix not in {f.lower() for f in settings.COVER_ALLOWED_FORMATS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{suffix}",
        )


def _assert_job_access(job, current_user: Optional[User]) -> None:
    if job.user_id is not None and (current_user is None or current_user.id != job.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this job")


@router.post(
    "/jobs",
    response_model=CoverCreateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    summary="Create a new AI cover job",
)
async def create_cover(
    reference_voice: UploadFile = File(..., description="Reference voice audio"),
    song: UploadFile = File(..., description="Song audio to convert"),
    model_id: Optional[str] = Form(default=None, description="Model identifier to use"),
    pitch_shift: int = Form(default=0, ge=-24, le=24, description="Semitone shift"),
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
) -> CoverCreateResponse:
    if not settings.COVER_SEPARATE_CMD_TEMPLATE or not settings.COVER_INFER_CMD_TEMPLATE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "cover runtime is not configured. Set COVER_SEPARATE_CMD_TEMPLATE and "
                "COVER_INFER_CMD_TEMPLATE in environment first."
            ),
        )

    _validate_audio_upload(reference_voice)
    _validate_audio_upload(song)

    job_id = uuid.uuid4()
    base_dir = _job_base_dir(job_id)
    input_dir = base_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    voice_ext = Path(reference_voice.filename or "reference.wav").suffix or ".wav"
    song_ext = Path(song.filename or "song.wav").suffix or ".wav"
    voice_path = input_dir / f"reference_voice{voice_ext}"
    song_path = input_dir / f"song{song_ext}"

    try:
        with voice_path.open("wb") as f:
            shutil.copyfileobj(reference_voice.file, f)
        with song_path.open("wb") as f:
            shutil.copyfileobj(song.file, f)
    except Exception as exc:
        logger.exception("failed to save uploaded files")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    job = await create_cover_job(
        session,
        job_id=job_id,
        user_id=current_user.id if current_user else None,
        input_voice_path=str(voice_path),
        input_song_path=str(song_path),
        model_id=model_id,
        pitch_shift=pitch_shift,
    )

    task_result = run_cover_job.delay(str(job.id))
    job = await update_cover_job(session, job_id=job.id, task_id=task_result.id)

    return CoverCreateResponse(
        job_id=str(job.id),
        task_id=job.task_id,
        status=CoverJobStatusEnum(job.status),
        stage=CoverJobStageEnum(job.stage),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=CoverJobStatusResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
    },
    summary="Get cover job status",
)
async def get_cover_status(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
) -> CoverJobStatusResponse:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id")

    job = await get_cover_job(session, job_uuid)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _assert_job_access(job, current_user)

    return CoverJobStatusResponse(
        job_id=str(job.id),
        status=CoverJobStatusEnum(job.status),
        stage=CoverJobStageEnum(job.stage),
        progress=job.progress,
        task_id=job.task_id,
        model_id=job.model_id,
        pitch_shift=job.pitch_shift,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@router.get(
    "/jobs/{job_id}/result",
    summary="Download generated cover result",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
    },
)
async def get_cover_result(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id")

    job = await get_cover_job(session, job_uuid)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _assert_job_access(job, current_user)

    if job.status != "succeeded":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Job status is {job.status}")
    if not job.output_mix_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result file missing")

    result_path = Path(job.output_mix_path)
    if not result_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result file not found")

    return FileResponse(path=result_path, media_type="audio/wav", filename=f"{job.id}.wav")


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=CoverCancelResponse,
    summary="Cancel an in-flight cover job",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
    },
)
async def cancel_cover_job(
    job_id: str,
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
) -> CoverCancelResponse:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id")

    job = await get_cover_job(session, job_uuid)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    _assert_job_access(job, current_user)

    if job.task_id:
        celery_app.control.revoke(job.task_id, terminate=True, signal="SIGTERM")

    job = await update_cover_job(session, job_id=job.id, status="canceled", stage="finalize", progress=100)

    return CoverCancelResponse(
        job_id=str(job.id),
        status=CoverJobStatusEnum(job.status),
        message="Job cancellation requested",
    )
