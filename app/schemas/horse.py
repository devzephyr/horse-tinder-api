from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TemperamentEnum(str, Enum):
    GENTLE = "gentle"
    SPIRITED = "spirited"
    CALM = "calm"
    PLAYFUL = "playful"
    BOLD = "bold"


class HorsePhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    is_primary: bool
    display_order: int
    created_at: datetime


class HorseCreate(BaseModel):
    name: str = Field(max_length=100)
    breed: str = Field(max_length=100)
    age: int = Field(ge=0, le=50)
    temperament: TemperamentEnum
    bio: str | None = Field(None, max_length=2000)
    location_city: str = Field(max_length=100)
    location_state: str | None = Field(None, max_length=100)
    location_country: str = Field(max_length=100)


class HorseUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    breed: str | None = Field(None, max_length=100)
    age: int | None = Field(None, ge=0, le=50)
    temperament: TemperamentEnum | None = None
    bio: str | None = Field(None, max_length=2000)
    location_city: str | None = Field(None, max_length=100)
    location_state: str | None = Field(None, max_length=100)
    location_country: str | None = Field(None, max_length=100)


class HorseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    breed: str
    age: int
    temperament: str
    bio: str | None
    location_city: str
    location_state: str | None
    location_country: str
    photos: list[HorsePhotoRead]
    is_active: bool
    created_at: datetime


class HorseBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    breed: str
    age: int
    temperament: str
    location_city: str
    location_country: str


class PhotoCreate(BaseModel):
    url: str = Field(max_length=2048)
    is_primary: bool = False
    display_order: int = Field(default=0, ge=0, le=9)


class PhotoUpdate(BaseModel):
    is_primary: bool | None = None
    display_order: int | None = Field(None, ge=0, le=9)
