from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.horse import HorseCreate, HorseRead, HorseUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import horse_service

router = APIRouter(prefix="/horses", tags=["horses"])


@router.post("/", response_model=HorseRead, status_code=201)
async def create_horse(
    data: HorseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    horse = await horse_service.create_horse(db, user.id, data)
    return horse


@router.get("/", response_model=PaginatedResponse[HorseRead])
async def list_horses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    horses, total = await horse_service.list_user_horses(db, user.id, offset, page_size)
    return PaginatedResponse(
        items=horses, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/{horse_id}", response_model=HorseRead)
async def get_horse(
    horse_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await horse_service.get_horse(db, horse_id)


@router.patch("/{horse_id}", response_model=HorseRead)
async def update_horse(
    horse_id: UUID,
    data: HorseUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    horse = await horse_service.get_horse_for_owner(db, horse_id, user.id)
    return await horse_service.update_horse(db, horse, data)


@router.delete("/{horse_id}", status_code=204)
async def delete_horse(
    horse_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    horse = await horse_service.get_horse_for_owner(db, horse_id, user.id)
    await horse_service.delete_horse(db, horse)
