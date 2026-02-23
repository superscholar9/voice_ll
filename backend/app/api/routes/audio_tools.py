"""Audio tools API routes."""
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.security import verify_api_key
from app.core.config import settings
from app.models.schemas import AudioInfoResponse, AudioConvertRequest, ErrorResponse
from app.services.audio_tools import (
    get_audio_info,
    convert_audio_format,
    adjust_audio_speed,
    adjust_audio_volume,
    concatenate_audio,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post(
    "/info",
    response_model=AudioInfoResponse,
    summary="Get audio file information",
    description="Extract metadata from an audio file",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def get_audio_file_info(
    audio_file: UploadFile = File(..., description="Audio file to analyze"),
    api_key: str = Depends(verify_api_key),
) -> AudioInfoResponse:
    """
    Get information about an audio file.

    Args:
        audio_file: Audio file to analyze
        api_key: API key for authentication

    Returns:
        Audio file information
    """
    try:
        # Validate file format
        if audio_file.content_type and not audio_file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {audio_file.content_type}. Expected audio file.",
            )

        # Check file size
        file_content = await audio_file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Get audio info
        info = await get_audio_info(file_content)

        logger.info(f"Audio info extracted: {info}")

        return AudioInfoResponse(
            filename=audio_file.filename or "unknown",
            format=info.get("format", "unknown"),
            duration_seconds=info["duration_seconds"],
            channels=info["channels"],
            sample_rate=info["sample_rate"],
            file_size_bytes=info["file_size_bytes"],
        )

    except ValueError as e:
        logger.error(f"Invalid audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error processing audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process audio file",
        )


@router.post(
    "/convert",
    summary="Convert audio format",
    description="Convert audio file to a different format",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def convert_audio(
    audio_file: UploadFile = File(..., description="Audio file to convert"),
    target_format: str = Form(..., description="Target format (wav, mp3, flac, ogg)"),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """
    Convert audio to a different format.

    Args:
        audio_file: Audio file to convert
        target_format: Target format
        api_key: API key for authentication

    Returns:
        Converted audio file
    """
    try:
        # Validate target format
        allowed_formats = ["wav", "mp3", "flac", "ogg"]
        if target_format.lower() not in allowed_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format. Allowed: {', '.join(allowed_formats)}",
            )

        # Check file size
        file_content = await audio_file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Convert audio
        converted_data, fmt = await convert_audio_format(file_content, target_format.lower())

        logger.info(f"Audio converted to {fmt}, size: {len(converted_data)} bytes")

        return Response(
            content=converted_data,
            media_type=f"audio/{fmt}",
            headers={
                "Content-Disposition": f'attachment; filename="converted.{fmt}"',
            },
        )

    except ValueError as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error converting audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert audio",
        )


@router.post(
    "/adjust-speed",
    summary="Adjust audio playback speed",
    description="Change the playback speed of audio",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def adjust_speed(
    audio_file: UploadFile = File(..., description="Audio file"),
    speed_factor: float = Form(..., ge=0.5, le=2.0, description="Speed multiplier (0.5-2.0)"),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """
    Adjust audio playback speed.

    Args:
        audio_file: Audio file
        speed_factor: Speed multiplier
        api_key: API key for authentication

    Returns:
        Audio with adjusted speed
    """
    try:
        # Check file size
        file_content = await audio_file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Adjust speed
        adjusted_data = await adjust_audio_speed(file_content, speed_factor)

        logger.info(f"Audio speed adjusted by {speed_factor}x")

        return Response(
            content=adjusted_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="speed_adjusted.wav"',
            },
        )

    except ValueError as e:
        logger.error(f"Speed adjustment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error adjusting speed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust audio speed",
        )


@router.post(
    "/adjust-volume",
    summary="Adjust audio volume",
    description="Change the volume level of audio",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def adjust_volume(
    audio_file: UploadFile = File(..., description="Audio file"),
    volume_db: float = Form(..., ge=-20, le=20, description="Volume adjustment in dB (-20 to +20)"),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """
    Adjust audio volume.

    Args:
        audio_file: Audio file
        volume_db: Volume adjustment in dB
        api_key: API key for authentication

    Returns:
        Audio with adjusted volume
    """
    try:
        # Check file size
        file_content = await audio_file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Adjust volume
        adjusted_data = await adjust_audio_volume(file_content, volume_db)

        logger.info(f"Audio volume adjusted by {volume_db}dB")

        return Response(
            content=adjusted_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="volume_adjusted.wav"',
            },
        )

    except ValueError as e:
        logger.error(f"Volume adjustment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Error adjusting volume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust audio volume",
        )
