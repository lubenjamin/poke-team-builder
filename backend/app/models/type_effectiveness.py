from sqlalchemy import Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TypeEffectiveness(Base):
    """The type matchup chart, ingested from PokeAPI's /type endpoint rather
    than hardcoded — a future new type just shows up correctly on the next
    sync. Plain strings for attacking_type/defending_type (not FK'd to a
    separate type table), matching the existing convention where
    pokemon.types and move.type already store raw type-name strings. Every
    pair is materialized explicitly, including implied 1x relations, so a
    lookup never needs "missing row = neutral" special-casing."""

    __tablename__ = "type_effectiveness"
    __table_args__ = (
        UniqueConstraint(
            "attacking_type", "defending_type", name="uq_type_effectiveness_pair"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attacking_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    defending_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False)
