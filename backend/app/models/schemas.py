"""Pydantic schemas for request/response validation."""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum


class LanguageEnum(str, Enum):
    """Supported languages for synthesis."""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    AUTO = "auto"


class SynthesizeRequest(BaseModel):
    """Request schema for voice synthesis."""

    text: str = Field(
        ...,
        description="Text to synthesize",
        min_length=1,
        max_length=5000
    )

    reference_audio_url: Optional[str] = Field(
        None,
        description="URL to reference audio file (if not uploading)"
    )

    language: LanguageEnum = Field(
        default=LanguageEnum.AUTO,
        description="Target language for synthesis"
    )

    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed multiplier (0.5-2.0)"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Sampling temperature for variation (0.1-1.0)"
    )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not empty after stripping."""
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class SynthesizeResponse(BaseModel):
    """Response schema for voice synthesis."""

    success: bool = Field(
        ...,
        description="Whether synthesis was successful"
    )

    audio_url: Optional[str] = Field(
        None,
        description="URL to download synthesized audio"
    )

    audio_format: Optional[str] = Field(
        None,
        description="Audio file format (wav, mp3, etc.)"
    )

    duration_seconds: Optional[float] = Field(
        None,
        description="Duration of synthesized audio in seconds"
    )

    message: Optional[str] = Field(
        None,
        description="Additional information or error message"
    )


class ErrorResponse(BaseModel):
    """Error response schema."""

    success: bool = Field(
        default=False,
        description="Always false for errors"
    )

    error: str = Field(
        ...,
        description="Error type or code"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    details: Optional[dict] = Field(
        None,
        description="Additional error details"
    )


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(
        ...,
        description="Service status (healthy, degraded, unhealthy)"
    )

    version: str = Field(
        ...,
        description="API version"
    )

    sovits_available: bool = Field(
        ...,
        description="Whether GPT-SoVITS service is reachable"
    )

    uptime_seconds: float = Field(
        ...,
        description="Service uptime in seconds"
    )


class TTSRequest(BaseModel):
    """Request schema for text-to-speech without voice cloning."""

    text: str = Field(
        ...,
        description="Text to synthesize",
        min_length=1,
        max_length=5000
    )

    language: LanguageEnum = Field(
        default=LanguageEnum.AUTO,
        description="Target language for synthesis"
    )

    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed multiplier (0.5-2.0)"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Sampling temperature for variation (0.1-1.0)"
    )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not empty after stripping."""
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class AudioInfoResponse(BaseModel):
    """Response schema for audio file information."""

    filename: str = Field(
        ...,
        description="Audio filename"
    )

    format: str = Field(
        ...,
        description="Audio format (wav, mp3, etc.)"
    )

    duration_seconds: float = Field(
        ...,
        description="Audio duration in seconds"
    )

    channels: int = Field(
        ...,
        description="Number of audio channels"
    )

    sample_rate: int = Field(
        ...,
        description="Sample rate in Hz"
    )

    file_size_bytes: int = Field(
        ...,
        description="File size in bytes"
    )


class AudioConvertRequest(BaseModel):
    """Request schema for audio format conversion."""

    target_format: str = Field(
        ...,
        description="Target audio format"
    )

    @field_validator('target_format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate target format is supported."""
        allowed_formats = ['wav', 'mp3', 'flac', 'ogg']
        v_lower = v.lower()
        if v_lower not in allowed_formats:
            raise ValueError(f"Format must be one of: {', '.join(allowed_formats)}")
        return v_lower


class HistoryItemResponse(BaseModel):
    """Response schema for a single history item."""

    id: str = Field(
        ...,
        description="Unique history item ID"
    )

    job_type: str = Field(
        ...,
        description="Type of job (clone or tts)"
    )

    status: str = Field(
        ...,
        description="Job status (success or error)"
    )

    input_text: str = Field(
        ...,
        description="Input text that was synthesized"
    )

    language: str = Field(
        ...,
        description="Language used for synthesis"
    )

    speed: float = Field(
        ...,
        description="Speed parameter used"
    )

    temperature: float = Field(
        ...,
        description="Temperature parameter used"
    )

    duration_seconds: Optional[float] = Field(
        None,
        description="Duration of generated audio in seconds"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )

    created_at: str = Field(
        ...,
        description="Timestamp when job was created"
    )


class HistoryListResponse(BaseModel):
    """Response schema for history list."""

    items: List[HistoryItemResponse] = Field(
        ...,
        description="List of history items"
    )

    total: int = Field(
        ...,
        description="Total number of history items"
    )


class CoverJobStatusEnum(str, Enum):
    """Cover generation job statuses."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class CoverJobStageEnum(str, Enum):
    """Cover pipeline stages."""

    QUEUED = "queued"
    PREPROCESS = "preprocess"
    SEPARATE = "separate"
    INFER = "infer"
    MIX = "mix"
    FINALIZE = "finalize"


class CoverCreateResponse(BaseModel):
    """Response for created cover jobs."""

    job_id: str = Field(..., description="Cover job ID")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    status: CoverJobStatusEnum = Field(..., description="Current job status")
    stage: CoverJobStageEnum = Field(..., description="Current processing stage")


class CoverJobStatusResponse(BaseModel):
    """Response containing full status for one cover job."""

    model_config = ConfigDict(protected_namespaces=())

    job_id: str = Field(..., description="Cover job ID")
    status: CoverJobStatusEnum = Field(..., description="Current job status")
    stage: CoverJobStageEnum = Field(..., description="Current processing stage")
    progress: int = Field(..., ge=0, le=100, description="Pipeline progress percentage")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    model_id: Optional[str] = Field(None, description="Model identifier used for inference")
    pitch_shift: int = Field(..., description="Pitch shift setting used by this job")
    error_message: Optional[str] = Field(None, description="Error message when failed")
    created_at: str = Field(..., description="Creation time (ISO8601)")
    updated_at: str = Field(..., description="Last update time (ISO8601)")


class CoverCancelResponse(BaseModel):
    """Response for cancel operations."""

    job_id: str = Field(..., description="Cover job ID")
    status: CoverJobStatusEnum = Field(..., description="Updated job status")
    message: str = Field(..., description="Cancellation result message")
