from pydantic import BaseModel, Field

from app.schemas.horse import TemperamentEnum


class HorseSearchParams(BaseModel):
    breed: str | None = Field(None, max_length=100)
    min_age: int | None = Field(None, ge=0, le=50)
    max_age: int | None = Field(None, ge=0, le=50)
    temperament: TemperamentEnum | None = None
    location_country: str | None = Field(None, max_length=100)
    location_state: str | None = Field(None, max_length=100)
    location_city: str | None = Field(None, max_length=100)
