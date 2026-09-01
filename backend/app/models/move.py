from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Move(Base):
    """
    Local cache of PokeAPI move data. `id` is the PokeAPI move id.
    power/accuracy/effect_chance are legitimately nullable — status moves have no
    power, guaranteed-hit moves have no accuracy. pp is nullable too — Z-Moves
    and Max Moves (ids 10001+) have none of their own. Priority is signed 
    (can be negative) but always present, so it's the one numeric field that's NOT NULL.
    """

    __tablename__ = "move"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    damage_class: Mapped[str] = mapped_column(String, nullable=False)
    power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    effect_chance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effect_text: Mapped[str | None] = mapped_column(String, nullable=True)

    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
