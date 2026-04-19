from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.horse import HorsePhotoRead, PhotoCreate, PhotoUpdate
from app.services import horse_service, photo_service

router = APIRouter(prefix="/horses/{horse_id}/photos", tags=["horse-photos"])


@router.post("/", response_model=HorsePhotoRead, status_code=201)
async def add_photo(
    horse_id: UUID,
    data: PhotoCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    horse = await horse_service.get_horse_for_owner(db, horse_id, user.id)
    return await photo_service.add_photo(db, horse, data)


@router.get("/", response_model=list[HorsePhotoRead])
async def list_photos(
    horse_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await horse_service.get_horse(db, horse_id)
    return await photo_service.list_photos(db, horse_id)


@router.patch("/{photo_id}", response_model=HorsePhotoRead)
async def update_photo(
    horse_id: UUID,
    photo_id: UUID,
    data: PhotoUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await horse_service.get_horse_for_owner(db, horse_id, user.id)
    photo = await photo_service.get_photo_for_horse(db, photo_id, horse_id)
    return await photo_service.update_photo(db, photo, data)


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    horse_id: UUID,
    photo_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await horse_service.get_horse_for_owner(db, horse_id, user.id)
    photo = await photo_service.get_photo_for_horse(db, photo_id, horse_id)
    await photo_service.delete_photo(db, photo)
