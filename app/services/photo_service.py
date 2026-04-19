from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, RateLimitException, ValidationException
from app.core.url_validator import validate_image_url
from app.models.horse import Horse, HorsePhoto
from app.schemas.horse import PhotoCreate, PhotoUpdate

MAX_PHOTOS_PER_HORSE = 10


async def add_photo(
    db: AsyncSession, horse: Horse, data: PhotoCreate
) -> HorsePhoto:
    count_result = await db.execute(
        select(func.count(HorsePhoto.id)).where(HorsePhoto.horse_id == horse.id)
    )
    count = count_result.scalar() or 0
    if count >= MAX_PHOTOS_PER_HORSE:
        raise RateLimitException(f"Maximum of {MAX_PHOTOS_PER_HORSE} photos per horse")

    is_valid, message = await validate_image_url(data.url)
    if not is_valid:
        raise ValidationException(f"Invalid image URL: {message}")

    photo = HorsePhoto(horse_id=horse.id, **data.model_dump())
    db.add(photo)
    await db.flush()
    return photo


async def list_photos(db: AsyncSession, horse_id: UUID) -> list[HorsePhoto]:
    result = await db.execute(
        select(HorsePhoto)
        .where(HorsePhoto.horse_id == horse_id)
        .order_by(HorsePhoto.display_order)
    )
    return list(result.scalars().all())


async def get_photo_for_horse(
    db: AsyncSession, photo_id: UUID, horse_id: UUID
) -> HorsePhoto:
    photo = (
        await db.execute(
            select(HorsePhoto).where(
                HorsePhoto.id == photo_id, HorsePhoto.horse_id == horse_id
            )
        )
    ).scalar_one_or_none()
    if not photo:
        raise NotFoundException("Photo not found")
    return photo


async def update_photo(db: AsyncSession, photo: HorsePhoto, data: PhotoUpdate) -> HorsePhoto:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(photo, key, value)
    await db.flush()
    return photo


async def delete_photo(db: AsyncSession, photo: HorsePhoto) -> None:
    await db.delete(photo)
    await db.flush()
