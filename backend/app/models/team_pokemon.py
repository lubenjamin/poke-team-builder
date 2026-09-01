from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TeamPokemon(Base):
    """
    Junction table for a team's ordered roster. `slot` (0-5) preserves order.
    """

    __tablename__ = "team_pokemon"
    __table_args__ = (UniqueConstraint("team_id", "slot", name="uq_team_pokemon_team_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)

    team: Mapped["Team"] = relationship(back_populates="roster")
    pokemon: Mapped["Pokemon"] = relationship()
    move_links: Mapped[list["TeamPokemonMove"]] = relationship(
        back_populates="team_pokemon", cascade="all, delete-orphan", order_by="TeamPokemonMove.slot"
    )

    @property
    def moves(self) -> list["Move"]:
        """The actual Move rows for this slot, in slot order — `move_links`
        is the raw join-table relationship (TeamPokemonMove), this flattens
        it to what callers actually want. Same pattern as Pokemon.pokedex_number."""
        return [link.move for link in self.move_links]
