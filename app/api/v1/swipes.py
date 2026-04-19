from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.swipe import RemainingSwipes, SwipeCreate, SwipeResult
from app.services import swipe_service

router = APIRouter(prefix="/swipes", tags=["swipes"])


@router.post("/", response_model=SwipeResult, status_code=201)
@limiter.limit("200/minute")
async def create_swipe(
    request: Request,
    data: SwipeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await swipe_service.create_swipe(db, user.id, data)


@router.get("/remaining", response_model=RemainingSwipes)
async def remaining_swipes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    remaining = await swipe_service.get_remaining_swipes(db, user.id)
    return RemainingSwipes(remaining=remaining)
