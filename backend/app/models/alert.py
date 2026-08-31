from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Alert(Base):
    """Materialized at detection time by the scan job; filtered against current
    team membership at read time (see docs/schema.md).

    Every alert stays scoped to a specific Pokemon-on-a-team (pokemon_id
    always set) regardless of what triggered it — that's true whether the
    Pokemon's own stats changed, a move it has equipped changed, or that move
    stopped being learnable and was unassigned. `move_id` is set for the
    latter two cases. Exactly one of pokemon_change_log_id/move_change_log_id
    is set for a "field changed" alert; both are null for a movepool-removal
    alert (self-explanatory via `message` alone)."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), nullable=False)
    move_id: Mapped[int | None] = mapped_column(ForeignKey("move.id"), nullable=True)
    pokemon_change_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("pokemon_change_log.id"), nullable=True
    )
    move_change_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("move_change_log.id"), nullable=True
    )
    message: Mapped[str] = mapped_column(String, nullable=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
