from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GameRecord(Base):
    __tablename__ = "games"

    game_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    player_color: Mapped[str] = mapped_column(String(5), nullable=False)
    bot_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="engine")
    bot_level: Mapped[int] = mapped_column(Integer, nullable=False)
    fen: Mapped[str] = mapped_column(Text, nullable=False)
    moves_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
