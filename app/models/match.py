import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Match(UUIDMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("horse_a_id", "horse_b_id", name="uq_match_pair"),
    )

    horse_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("horses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    horse_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("horses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    horse_a = relationship("Horse", foreign_keys=[horse_a_id])
    horse_b = relationship("Horse", foreign_keys=[horse_b_id])
    messages = relationship("Message", back_populates="match", lazy="noload")
