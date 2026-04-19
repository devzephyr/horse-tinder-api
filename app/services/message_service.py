from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, RateLimitException
from app.models.message import Message
from app.models.notification import Notification
from app.services.match_service import get_match_for_user

MESSAGE_COOLDOWN_SECONDS = 1


async def send_message(
    db: AsyncSession, match_id: UUID, sender_id: UUID, content: str
) -> Message:
    match = await get_match_for_user(db, match_id, sender_id)

    cooldown_cutoff = datetime.now(timezone.utc) - timedelta(seconds=MESSAGE_COOLDOWN_SECONDS)
    recent = (
        await db.execute(
            select(Message).where(
                Message.match_id == match_id,
                Message.sender_id == sender_id,
                Message.created_at > cooldown_cutoff,
            )
        )
    ).scalar_one_or_none()

    if recent:
        raise RateLimitException("Please wait before sending another message")

    message = Message(match_id=match_id, sender_id=sender_id, content=content)
    db.add(message)
    await db.flush()

    recipient_horse = match.horse_b if match.horse_a.owner_id == sender_id else match.horse_a
    db.add(Notification(
        user_id=recipient_horse.owner_id,
        type="new_message",
        title="New Message",
        body=f"You have a new message in your match",
        reference_id=message.id,
    ))

    return message


async def list_messages(
    db: AsyncSession, match_id: UUID, user_id: UUID, offset: int, limit: int
) -> tuple[list[Message], int]:
    await get_match_for_user(db, match_id, user_id)

    total_result = await db.execute(
        select(func.count(Message.id)).where(Message.match_id == match_id)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Message)
        .where(Message.match_id == match_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def mark_read(db: AsyncSession, message_id: UUID, user_id: UUID) -> Message:
    message = (
        await db.execute(select(Message).where(Message.id == message_id))
    ).scalar_one_or_none()

    if not message:
        raise NotFoundException("Message not found")

    await get_match_for_user(db, message.match_id, user_id)

    if message.sender_id == user_id:
        raise NotFoundException("Message not found")

    message.read_at = datetime.now(timezone.utc)
    await db.flush()
    return message
