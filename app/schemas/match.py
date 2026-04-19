from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.horse import HorseBriefRead


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    horse_a_id: UUID
    horse_b_id: UUID
    matched_at: datetime
    is_active: bool


class MatchDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    horse_a: HorseBriefRead
    horse_b: HorseBriefRead
    matched_at: datetime
    is_active: bool
