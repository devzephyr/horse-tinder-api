from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.match import MatchDetailRead
from app.schemas.pagination import PaginatedResponse
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/", response_model=PaginatedResponse[MatchDetailRead])
async def list_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    matches, total = await match_service.list_user_matches(db, user.id, offset, page_size)
    return PaginatedResponse(
        items=matches, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/{match_id}", response_model=MatchDetailRead)
async def get_match(
    match_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await match_service.get_match_for_user(db, match_id, user.id)


@router.delete("/{match_id}", status_code=204)
async def unmatch(
    match_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    match = await match_service.get_match_for_user(db, match_id, user.id)
    await match_service.unmatch(db, match)
