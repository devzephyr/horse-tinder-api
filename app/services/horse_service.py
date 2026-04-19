from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, RateLimitException
from app.models.horse import Horse
from app.schemas.horse import HorseCreate, HorseUpdate

MAX_HORSES_PER_USER = 5


async def create_horse(db: AsyncSession, owner_id: UUID, data: HorseCreate) -> Horse:
    count_result = await db.execute(
        select(func.count(Horse.id)).where(Horse.owner_id == owner_id, Horse.is_active == True)  # noqa: E712
    )
    count = count_result.scalar() or 0
    if count >= MAX_HORSES_PER_USER:
        raise RateLimitException(f"Maximum of {MAX_HORSES_PER_USER} horses per user")

    horse = Horse(owner_id=owner_id, **data.model_dump())
    db.add(horse)
    await db.flush()
    await db.refresh(horse, attribute_names=["photos"])
    return horse


async def get_horse(db: AsyncSession, horse_id: UUID) -> Horse:
    horse = (
        await db.execute(select(Horse).where(Horse.id == horse_id, Horse.is_active == True))  # noqa: E712
    ).scalar_one_or_none()
    if not horse:
        raise NotFoundException("Horse not found")
    return horse


async def get_horse_for_owner(db: AsyncSession, horse_id: UUID, owner_id: UUID) -> Horse:
    horse = (
        await db.execute(
            select(Horse).where(Horse.id == horse_id, Horse.owner_id == owner_id)
        )
    ).scalar_one_or_none()
    if not horse:
        raise NotFoundException("Horse not found")
    return horse


async def list_user_horses(
    db: AsyncSession, owner_id: UUID, offset: int, limit: int
) -> tuple[list[Horse], int]:
    total_result = await db.execute(
        select(func.count(Horse.id)).where(Horse.owner_id == owner_id)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Horse)
        .where(Horse.owner_id == owner_id)
        .order_by(Horse.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def update_horse(db: AsyncSession, horse: Horse, data: HorseUpdate) -> Horse:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(horse, key, value)
    await db.flush()
    await db.refresh(horse, attribute_names=["photos"])
    return horse


async def delete_horse(db: AsyncSession, horse: Horse) -> None:
    horse.is_active = False
    await db.flush()
