from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.models.horse import Horse
from app.models.match import Match
from app.models.notification import Notification
from app.models.swipe import Swipe
from app.schemas.swipe import SwipeCreate, SwipeResult

DAILY_SWIPE_LIMIT = 100


async def get_remaining_swipes(db: AsyncSession, user_id: UUID) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(Swipe.id))
        .join(Horse, Swipe.swiper_horse_id == Horse.id)
        .where(Horse.owner_id == user_id, Swipe.created_at >= today_start)
    )
    count = count_result.scalar() or 0
    return max(0, DAILY_SWIPE_LIMIT - count)


async def create_swipe(
    db: AsyncSession, user_id: UUID, data: SwipeCreate
) -> SwipeResult:
    swiper_horse = (
        await db.execute(
            select(Horse).where(Horse.id == data.swiper_horse_id, Horse.owner_id == user_id)
        )
    ).scalar_one_or_none()
    if not swiper_horse:
        raise NotFoundException("Horse not found")

    swiped_horse = (
        await db.execute(
            select(Horse).where(Horse.id == data.swiped_horse_id, Horse.is_active == True)  # noqa: E712
        )
    ).scalar_one_or_none()
    if not swiped_horse:
        raise NotFoundException("Target horse not found")

    if data.swiper_horse_id == data.swiped_horse_id:
        raise ValidationException("Cannot swipe on your own horse")

    if swiped_horse.owner_id == user_id:
        raise ValidationException("Cannot swipe on your own horse")

    existing = (
        await db.execute(
            select(Swipe).where(
                Swipe.swiper_horse_id == data.swiper_horse_id,
                Swipe.swiped_horse_id == data.swiped_horse_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictException("Already swiped on this horse")

    remaining = await get_remaining_swipes(db, user_id)
    if remaining <= 0:
        raise RateLimitException("Daily swipe limit reached")

    swipe = Swipe(
        swiper_horse_id=data.swiper_horse_id,
        swiped_horse_id=data.swiped_horse_id,
        direction=data.direction.value,
    )
    db.add(swipe)
    await db.flush()

    is_match = False
    match_id = None

    if data.direction.value == "like":
        reciprocal = (
            await db.execute(
                select(Swipe).where(
                    Swipe.swiper_horse_id == data.swiped_horse_id,
                    Swipe.swiped_horse_id == data.swiper_horse_id,
                    Swipe.direction == "like",
                )
            )
        ).scalar_one_or_none()

        if reciprocal:
            a_id, b_id = sorted([data.swiper_horse_id, data.swiped_horse_id])
            match = Match(horse_a_id=a_id, horse_b_id=b_id)
            db.add(match)
            await db.flush()
            is_match = True
            match_id = match.id

            for horse in [swiper_horse, swiped_horse]:
                db.add(Notification(
                    user_id=horse.owner_id,
                    type="new_match",
                    title="New Match!",
                    body=f"{swiper_horse.name} and {swiped_horse.name} matched!",
                    reference_id=match.id,
                ))

    from app.schemas.swipe import SwipeRead

    swipe_read = SwipeRead.model_validate(swipe)
    return SwipeResult(swipe=swipe_read, is_match=is_match, match_id=match_id)
