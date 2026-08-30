from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PokemonMovepool(Base):
    """Join table: which moves a given form can learn. FKs the per-form `pokemon`
    table (not `pokemon_species`) since PokeAPI's movepool is defined per form —
    two forms of the same species can legitimately learn different moves."""

    __tablename__ = "pokemon_movepool"
    __table_args__ = (
        UniqueConstraint("pokemon_id", "move_id", name="uq_pokemon_movepool_pokemon_move"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    move_id: Mapped[int] = mapped_column(
        ForeignKey("move.id", ondelete="CASCADE"), nullable=False, index=True
    )

    pokemon: Mapped["Pokemon"] = relationship()
    move: Mapped["Move"] = relationship()
