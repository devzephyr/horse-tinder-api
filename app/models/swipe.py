import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Swipe(UUIDMixin, Base):
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("swiper_horse_id", "swiped_horse_id", name="uq_swipe_pair"),
    )

    swiper_horse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("horses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    swiped_horse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("horses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    swiper_horse = relationship("Horse", foreign_keys=[swiper_horse_id])
    swiped_horse = relationship("Horse", foreign_keys=[swiped_horse_id])
