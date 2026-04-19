from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.horse import HorseRead
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserAdminRead
from app.services import horse_service, user_service

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/users", response_model=PaginatedResponse[UserAdminRead])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    users, total = await user_service.admin_list_users(db, offset, page_size)
    return PaginatedResponse(
        items=users, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/users/{user_id}", response_model=UserAdminRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_user(db, user_id)


@router.patch("/users/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    allowed_fields = {"is_active", "is_locked", "role"}
    filtered = {k: v for k, v in data.items() if k in allowed_fields}
    return await user_service.admin_update_user(db, user_id, filtered)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await user_service.admin_delete_user(db, user_id)


@router.get("/horses", response_model=PaginatedResponse[HorseRead])
async def list_all_horses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func, select
    from app.models.horse import Horse

    offset = (page - 1) * page_size
    total_result = await db.execute(select(func.count(Horse.id)))
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Horse).order_by(Horse.created_at.desc()).offset(offset).limit(page_size)
    )
    horses = list(result.scalars().all())
    return PaginatedResponse(
        items=horses, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.patch("/horses/{horse_id}", response_model=HorseRead)
async def moderate_horse(
    horse_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    from app.models.horse import Horse
    from sqlalchemy import select

    horse = (await db.execute(select(Horse).where(Horse.id == horse_id))).scalar_one_or_none()
    if not horse:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Horse not found")

    allowed_fields = {"is_active"}
    for key, value in data.items():
        if key in allowed_fields:
            setattr(horse, key, value)
    await db.flush()
    return horse
