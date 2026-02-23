"""GPT-SoVITS client service for voice synthesis."""

import logging
import httpx
from typing import Optional, BinaryIO
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


class SoVITSClient:
    """Client for interacting with GPT-SoVITS service."""

    def __init__(self):
        """Initialize SoVITS client."""
        self.base_url = settings.SOVITS_BASE_URL
        self.timeout = settings.SOVITS_TIMEOUT

    async def health_check(self) -> bool:
        """
        Check if GPT-SoVITS service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"SoVITS health check failed: {e}")
            return False

    async def synthesize(
        self,
        text: str,
        reference_audio: BinaryIO,
        language: str = "auto",
        speed: float = 1.0,
        temperature: float = 0.7,
    ) -> bytes:
        """
        Synthesize speech from text using reference audio.

        Args:
            text: Text to synthesize
            reference_audio: Reference audio file object
            language: Target language code
            speed: Speech speed multiplier
            temperature: Sampling temperature

        Returns:
            Audio data as bytes

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response is invalid
        """
        try:
            # Prepare multipart form data
            files = {
                "reference_audio": ("reference.wav", reference_audio, "audio/wav")
            }

            data = {
                "text": text,
                "language": language,
                "speed": speed,
                "temperature": temperature,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending synthesis request to {self.base_url}")
                response = await client.post(
                    f"{self.base_url}/synthesize",
                    files=files,
                    data=data,
                )
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("audio/"):
                    logger.error(f"Unexpected content type: {content_type}")
                    raise ValueError(f"Expected audio response, got {content_type}")

                return response.content

        except httpx.TimeoutException as e:
            logger.error(f"SoVITS request timeout: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"SoVITS HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"SoVITS synthesis error: {e}")
            raise

    async def synthesize_tts(
        self,
        text: str,
        language: str = "auto",
        speed: float = 1.0,
        temperature: float = 0.7,
    ) -> bytes:
        """
        Synthesize speech from text without reference audio (uses default voice).

        Args:
            text: Text to synthesize
            language: Target language code
            speed: Speech speed multiplier
            temperature: Sampling temperature

        Returns:
            Audio data as bytes

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response is invalid
        """
        try:
            data = {
                "text": text,
                "language": language,
                "speed": speed,
                "temperature": temperature,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending TTS request to {self.base_url}")
                response = await client.post(f"{self.base_url}/tts", data=data)
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("audio/"):
                    logger.error(f"Unexpected content type: {content_type}")
                    raise ValueError(f"Expected audio response, got {content_type}")

                return response.content

        except httpx.TimeoutException as e:
            logger.error(f"SoVITS TTS request timeout: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"SoVITS TTS HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"SoVITS TTS error: {e}")
            raise


# Global client instance
sovits_client = SoVITSClient()
