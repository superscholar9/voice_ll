"""Audio processing tools service."""
import io
import logging
from typing import Tuple
from pydub import AudioSegment

logger = logging.getLogger(__name__)


async def get_audio_info(audio_data: bytes) -> dict:
    """
    Extract audio information from audio data.

    Args:
        audio_data: Raw audio file bytes

    Returns:
        Dictionary with audio information
    """
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        return {
            "duration_seconds": len(audio) / 1000.0,
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "file_size_bytes": len(audio_data),
            "format": audio.format if hasattr(audio, 'format') else "unknown",
        }
    except Exception as e:
        logger.error(f"Error extracting audio info: {e}")
        raise ValueError(f"Failed to extract audio information: {str(e)}")


async def convert_audio_format(
    audio_data: bytes,
    target_format: str,
) -> Tuple[bytes, str]:
    """
    Convert audio to target format.

    Args:
        audio_data: Raw audio file bytes
        target_format: Target format (wav, mp3, flac, ogg)

    Returns:
        Tuple of (converted audio bytes, format)
    """
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        output = io.BytesIO()
        audio.export(output, format=target_format)
        converted_data = output.getvalue()

        logger.info(f"Audio converted to {target_format}, size: {len(converted_data)} bytes")
        return converted_data, target_format

    except Exception as e:
        logger.error(f"Error converting audio format: {e}")
        raise ValueError(f"Failed to convert audio format: {str(e)}")


async def adjust_audio_speed(
    audio_data: bytes,
    speed_factor: float,
) -> bytes:
    """
    Adjust audio playback speed.

    Args:
        audio_data: Raw audio file bytes
        speed_factor: Speed multiplier (0.5-2.0)

    Returns:
        Audio bytes with adjusted speed
    """
    try:
        if speed_factor < 0.5 or speed_factor > 2.0:
            raise ValueError("Speed factor must be between 0.5 and 2.0")

        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        # Adjust speed by changing frame rate
        adjusted = audio.speedup(playback_speed=speed_factor)

        output = io.BytesIO()
        adjusted.export(output, format="wav")
        adjusted_data = output.getvalue()

        logger.info(f"Audio speed adjusted by {speed_factor}x, size: {len(adjusted_data)} bytes")
        return adjusted_data

    except Exception as e:
        logger.error(f"Error adjusting audio speed: {e}")
        raise ValueError(f"Failed to adjust audio speed: {str(e)}")


async def adjust_audio_volume(
    audio_data: bytes,
    volume_db: float,
) -> bytes:
    """
    Adjust audio volume.

    Args:
        audio_data: Raw audio file bytes
        volume_db: Volume adjustment in dB (-20 to +20)

    Returns:
        Audio bytes with adjusted volume
    """
    try:
        if volume_db < -20 or volume_db > 20:
            raise ValueError("Volume adjustment must be between -20 and +20 dB")

        audio = AudioSegment.from_file(io.BytesIO(audio_data))

        # Adjust volume
        adjusted = audio + volume_db

        output = io.BytesIO()
        adjusted.export(output, format="wav")
        adjusted_data = output.getvalue()

        logger.info(f"Audio volume adjusted by {volume_db}dB, size: {len(adjusted_data)} bytes")
        return adjusted_data

    except Exception as e:
        logger.error(f"Error adjusting audio volume: {e}")
        raise ValueError(f"Failed to adjust audio volume: {str(e)}")


async def concatenate_audio(
    audio_list: list[bytes],
) -> bytes:
    """
    Concatenate multiple audio files.

    Args:
        audio_list: List of audio file bytes

    Returns:
        Concatenated audio bytes
    """
    try:
        if not audio_list:
            raise ValueError("Audio list cannot be empty")

        combined = AudioSegment.empty()

        for audio_data in audio_list:
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            combined += audio

        output = io.BytesIO()
        combined.export(output, format="wav")
        combined_data = output.getvalue()

        logger.info(f"Audio concatenated, total size: {len(combined_data)} bytes")
        return combined_data

    except Exception as e:
        logger.error(f"Error concatenating audio: {e}")
        raise ValueError(f"Failed to concatenate audio: {str(e)}")
