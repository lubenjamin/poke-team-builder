from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TeamPokemonMove(Base):
    """Up to 4 moves selected for one roster slot. FKs `team_pokemon.id`, not
    `pokemon_id` — the same species could have a different moveset on a
    different team, or in a different slot."""

    __tablename__ = "team_pokemon_move"
    __table_args__ = (
        UniqueConstraint("team_pokemon_id", "slot", name="uq_team_pokemon_move_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("team_pokemon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    move_id: Mapped[int] = mapped_column(ForeignKey("move.id"), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)

    team_pokemon: Mapped["TeamPokemon"] = relationship(back_populates="move_links")
    move: Mapped["Move"] = relationship()
