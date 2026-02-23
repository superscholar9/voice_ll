"""Voice synthesis API routes."""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.security import verify_api_key
from app.core.config import settings
from app.db.session import get_async_session
from app.auth.deps import get_current_user_optional
from app.db.models import User
from app.models.schemas import (
    SynthesizeRequest,
    SynthesizeResponse,
    ErrorResponse,
    LanguageEnum,
)
from app.services.sovits_client import sovits_client
from app.services.history_service import record_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post(
    "/synthesize",
    response_model=SynthesizeResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    summary="Synthesize speech from text",
    description="Generate speech audio from text using a reference voice sample",
)
async def synthesize_voice(
    text: str = Form(..., description="Text to synthesize", min_length=1, max_length=5000),
    reference_audio: UploadFile = File(..., description="Reference audio file for voice cloning"),
    language: LanguageEnum = Form(default=LanguageEnum.AUTO, description="Target language"),
    speed: float = Form(default=1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)"),
    temperature: float = Form(default=0.7, ge=0.1, le=1.0, description="Sampling temperature (0.1-1.0)"),
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    """
    Synthesize speech from text using reference audio.

    Args:
        text: Text to convert to speech
        reference_audio: Audio file containing reference voice
        language: Target language for synthesis
        speed: Speech speed multiplier
        temperature: Sampling temperature for variation
        api_key: API key for authentication

    Returns:
        Audio file as binary response

    Raises:
        HTTPException: If synthesis fails
    """
    try:
        # Validate text
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )

        # Validate file format
        if reference_audio.content_type and not reference_audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {reference_audio.content_type}. Expected audio file."
            )

        # Check file size
        file_content = await reference_audio.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )

        # Reset file pointer
        await reference_audio.seek(0)

        logger.info(f"Synthesizing text (length: {len(text)}) with language: {language}")

        # Call SoVITS service
        audio_data = await sovits_client.synthesize(
            text=text.strip(),
            reference_audio=reference_audio.file,
            language=language.value,
            speed=speed,
            temperature=temperature,
        )

        logger.info(f"Synthesis successful, audio size: {len(audio_data)} bytes")

        # Record successful synthesis in history
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="clone",
            status="success",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            duration_seconds=len(audio_data) / 44100 / 2,
        )

        # Return audio as binary response
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="synthesized.wav"',
                "X-Audio-Duration": str(len(audio_data) / 44100 / 2),  # Approximate
            }
        )

    except httpx.TimeoutException:
        logger.error("SoVITS service timeout")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="clone",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message="Voice synthesis service timeout",
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Voice synthesis service timeout. Please try again."
        )
    except httpx.HTTPError as e:
        logger.error(f"SoVITS HTTP error: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="clone",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=f"Voice synthesis service error: {str(e)}",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Voice synthesis service error. Please try again later."
        )
    except ValueError as e:
        logger.error(f"Invalid response from SoVITS: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="clone",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error during synthesis: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="clone",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=f"Unexpected error: {str(e)}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during synthesis"
        )


@router.post(
    "/tts",
    summary="Text-to-speech synthesis",
    description="Generate speech from text using default voice",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def text_to_speech(
    text: str = Form(..., description="Text to synthesize", min_length=1, max_length=5000),
    language: LanguageEnum = Form(default=LanguageEnum.AUTO, description="Target language"),
    speed: float = Form(default=1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)"),
    temperature: float = Form(default=0.7, ge=0.1, le=1.0, description="Sampling temperature (0.1-1.0)"),
    api_key: str = Depends(verify_api_key),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    """
    Synthesize speech from text using default voice.

    Args:
        text: Text to convert to speech
        language: Target language for synthesis
        speed: Speech speed multiplier
        temperature: Sampling temperature for variation
        api_key: API key for authentication

    Returns:
        Audio file as binary response

    Raises:
        HTTPException: If synthesis fails
    """
    try:
        # Validate text
        if not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )

        logger.info(f"TTS request: text length={len(text)}, language={language}")

        # Call SoVITS service
        audio_data = await sovits_client.synthesize_tts(
            text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
        )

        logger.info(f"TTS successful, audio size: {len(audio_data)} bytes")

        # Record successful TTS in history
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="tts",
            status="success",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            duration_seconds=len(audio_data) / 44100 / 2,
        )

        # Return audio as binary response
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="tts_output.wav"',
                "X-Audio-Duration": str(len(audio_data) / 44100 / 2),  # Approximate
            }
        )

    except httpx.TimeoutException:
        logger.error("SoVITS TTS service timeout")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="tts",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message="TTS service timeout",
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="TTS service timeout. Please try again."
        )
    except httpx.HTTPError as e:
        logger.error(f"SoVITS TTS HTTP error: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="tts",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=f"TTS service error: {str(e)}",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TTS service error. Please try again later."
        )
    except ValueError as e:
        logger.error(f"Invalid response from SoVITS TTS: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="tts",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error during TTS: {e}")
        await record_history(
            session=session,
            user_id=current_user.id if current_user else None,
            job_type="tts",
            status="error",
            input_text=text.strip(),
            language=language.value,
            speed=speed,
            temperature=temperature,
            error_message=f"Unexpected error: {str(e)}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during TTS"
        )


@router.get(
    "/health",
    summary="Check voice service health",
    description="Verify that the voice synthesis service is available",
)
async def check_voice_health(
    api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Check if GPT-SoVITS service is available.

    Args:
        api_key: API key for authentication

    Returns:
        Health status information
    """
    is_healthy = await sovits_client.health_check()

    return {
        "service": "voice-synthesis",
        "status": "healthy" if is_healthy else "unhealthy",
        "sovits_available": is_healthy,
    }
