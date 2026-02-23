"""History API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.auth.deps import get_current_user
from app.db.models import User
from app.services.history_service import list_user_history
from app.models.schemas import HistoryItemResponse, HistoryListResponse

router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "",
    response_model=HistoryListResponse,
    summary="Get synthesis history",
    description="Retrieve synthesis history for the authenticated user",
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> HistoryListResponse:
    """
    Get synthesis history for the current user.

    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Authenticated user
        session: Database session

    Returns:
        List of history items with total count
    """
    items, total = await list_user_history(
        session, user_id=current_user.id, limit=limit, offset=offset
    )

    return HistoryListResponse(
        items=[
            HistoryItemResponse(
                id=str(h.id),
                job_type=h.job_type,
                status=h.status,
                input_text=h.input_text,
                language=h.language,
                speed=h.speed,
                temperature=h.temperature,
                duration_seconds=h.duration_seconds,
                error_message=h.error_message,
                created_at=h.created_at.isoformat(),
            )
            for h in items
        ],
        total=total,
    )
