from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.schemas.search import HorseSearchParams


async def search_horses(
    db: AsyncSession,
    params: HorseSearchParams,
    offset: int,
    limit: int,
) -> tuple[list[Horse], int]:
    query = select(Horse).where(Horse.is_active == True)  # noqa: E712

    if params.breed:
        query = query.where(Horse.breed.ilike(f"%{params.breed}%"))
    if params.min_age is not None:
        query = query.where(Horse.age >= params.min_age)
    if params.max_age is not None:
        query = query.where(Horse.age <= params.max_age)
    if params.temperament:
        query = query.where(Horse.temperament == params.temperament.value)
    if params.location_country:
        query = query.where(Horse.location_country.ilike(f"%{params.location_country}%"))
    if params.location_state:
        query = query.where(Horse.location_state.ilike(f"%{params.location_state}%"))
    if params.location_city:
        query = query.where(Horse.location_city.ilike(f"%{params.location_city}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(
        query.order_by(Horse.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
