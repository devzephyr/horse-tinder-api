from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.horse import HorseRead, TemperamentEnum
from app.schemas.pagination import PaginatedResponse
from app.schemas.search import HorseSearchParams
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/horses", response_model=PaginatedResponse[HorseRead])
async def search_horses(
    breed: str | None = Query(None, max_length=100),
    min_age: int | None = Query(None, ge=0, le=50),
    max_age: int | None = Query(None, ge=0, le=50),
    temperament: TemperamentEnum | None = None,
    location_country: str | None = Query(None, max_length=100),
    location_state: str | None = Query(None, max_length=100),
    location_city: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    params = HorseSearchParams(
        breed=breed, min_age=min_age, max_age=max_age,
        temperament=temperament, location_country=location_country,
        location_state=location_state, location_city=location_city,
    )
    offset = (page - 1) * page_size
    horses, total = await search_service.search_horses(db, params, offset, page_size)
    return PaginatedResponse(
        items=horses, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )
