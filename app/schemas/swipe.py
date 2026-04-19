from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SwipeDirection(str, Enum):
    LIKE = "like"
    PASS = "pass"


class SwipeCreate(BaseModel):
    swiper_horse_id: UUID
    swiped_horse_id: UUID
    direction: SwipeDirection


class SwipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    swiper_horse_id: UUID
    swiped_horse_id: UUID
    direction: str
    created_at: datetime


class SwipeResult(BaseModel):
    swipe: SwipeRead
    is_match: bool
    match_id: UUID | None = None


class RemainingSwipes(BaseModel):
    remaining: int
    limit: int = 100
