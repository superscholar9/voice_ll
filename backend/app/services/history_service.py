"""History service for recording and retrieving synthesis history."""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.db.models import SynthesisHistory
import uuid


async def record_history(
    session: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    job_type: str = "clone",
    status: str = "success",
    input_text: str = "",
    language: str = "auto",
    speed: float = 1.0,
    temperature: float = 0.7,
    duration_seconds: Optional[float] = None,
    error_message: Optional[str] = None,
) -> SynthesisHistory:
    """
    Record a synthesis job in history.

    Args:
        session: Database session
        user_id: User ID (optional for anonymous usage)
        job_type: Type of job ("clone" or "tts")
        status: Job status ("success" or "error")
        input_text: Text that was synthesized
        language: Language used
        speed: Speed parameter
        temperature: Temperature parameter
        duration_seconds: Duration of generated audio
        error_message: Error message if job failed

    Returns:
        Created history record
    """
    history = SynthesisHistory(
        user_id=user_id,
        job_type=job_type,
        status=status,
        input_text=input_text,
        language=language,
        speed=speed,
        temperature=temperature,
        duration_seconds=duration_seconds,
        error_message=error_message,
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history


async def list_user_history(
    session: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[SynthesisHistory], int]:
    """
    List synthesis history for a user.

    Args:
        session: Database session
        user_id: User ID to filter by (None for all users)
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        Tuple of (list of history items, total count)
    """
    # Build query for items
    query = select(SynthesisHistory).order_by(desc(SynthesisHistory.created_at))
    if user_id:
        query = query.where(SynthesisHistory.user_id == user_id)
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    items = result.scalars().all()

    # Count total
    count_query = select(func.count(SynthesisHistory.id))
    if user_id:
        count_query = count_query.where(SynthesisHistory.user_id == user_id)

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    return list(items), total
