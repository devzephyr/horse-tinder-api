from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.user import UserUpdate


async def get_user(db: AsyncSession, user_id: UUID) -> User:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return user
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.flush()
    return user


async def deactivate_user(db: AsyncSession, user: User) -> None:
    user.is_active = False
    await db.flush()


async def admin_list_users(
    db: AsyncSession, offset: int, limit: int
) -> tuple[list[User], int]:
    total_result = await db.execute(select(User))
    total = len(total_result.scalars().all())

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def admin_update_user(db: AsyncSession, user_id: UUID, data: dict) -> User:
    user = await get_user(db, user_id)
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await db.flush()
    return user


async def admin_delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await get_user(db, user_id)
    await db.delete(user)
    await db.flush()
