from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageRead
from app.schemas.pagination import PaginatedResponse
from app.services import message_service

router = APIRouter(prefix="/matches/{match_id}/messages", tags=["messages"])


@router.get("/", response_model=PaginatedResponse[MessageRead])
async def list_messages(
    match_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    messages, total = await message_service.list_messages(db, match_id, user.id, offset, page_size)
    return PaginatedResponse(
        items=messages, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("/", response_model=MessageRead, status_code=201)
@limiter.limit("60/minute")
async def send_message(
    request: Request,
    match_id: UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await message_service.send_message(db, match_id, user.id, data.content)


@router.patch("/{message_id}/read", response_model=MessageRead)
async def mark_read(
    match_id: UUID,
    message_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await message_service.mark_read(db, message_id, user.id)
