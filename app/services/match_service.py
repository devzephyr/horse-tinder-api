from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.horse import Horse
from app.models.match import Match


async def list_user_matches(
    db: AsyncSession, user_id: UUID, offset: int, limit: int
) -> tuple[list[Match], int]:
    user_horse_ids_subq = select(Horse.id).where(Horse.owner_id == user_id).subquery()

    base_filter = or_(
        Match.horse_a_id.in_(select(user_horse_ids_subq)),
        Match.horse_b_id.in_(select(user_horse_ids_subq)),
    )

    total_result = await db.execute(
        select(func.count(Match.id)).where(base_filter, Match.is_active == True)  # noqa: E712
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Match)
        .options(selectinload(Match.horse_a), selectinload(Match.horse_b))
        .where(base_filter, Match.is_active == True)  # noqa: E712
        .order_by(Match.matched_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def get_match_for_user(db: AsyncSession, match_id: UUID, user_id: UUID) -> Match:
    user_horse_ids_subq = select(Horse.id).where(Horse.owner_id == user_id).subquery()

    match = (
        await db.execute(
            select(Match)
            .options(selectinload(Match.horse_a), selectinload(Match.horse_b))
            .where(
                Match.id == match_id,
                or_(
                    Match.horse_a_id.in_(select(user_horse_ids_subq)),
                    Match.horse_b_id.in_(select(user_horse_ids_subq)),
                ),
            )
        )
    ).scalar_one_or_none()

    if not match:
        raise NotFoundException("Match not found")
    return match


async def unmatch(db: AsyncSession, match: Match) -> None:
    match.is_active = False
    await db.flush()


async def user_is_match_participant(db: AsyncSession, match_id: UUID, user_id: UUID) -> bool:
    user_horse_ids_subq = select(Horse.id).where(Horse.owner_id == user_id).subquery()

    result = await db.execute(
        select(Match.id).where(
            Match.id == match_id,
            Match.is_active == True,  # noqa: E712
            or_(
                Match.horse_a_id.in_(select(user_horse_ids_subq)),
                Match.horse_b_id.in_(select(user_horse_ids_subq)),
            ),
        )
    )
    return result.scalar_one_or_none() is not None
