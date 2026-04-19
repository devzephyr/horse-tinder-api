import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Horse(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "horses"
    __table_args__ = (CheckConstraint("age >= 0 AND age <= 50", name="ck_horse_age"),)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    breed: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    temperament: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_city: Mapped[str] = mapped_column(String(100), nullable=False)
    location_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    owner = relationship("User", back_populates="horses")
    photos = relationship(
        "HorsePhoto", back_populates="horse", lazy="selectin", cascade="all, delete-orphan"
    )


class HorsePhoto(UUIDMixin, Base):
    __tablename__ = "horse_photos"

    horse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("horses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    horse = relationship("Horse", back_populates="photos")
