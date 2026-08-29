from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TeamPokemon(Base):
    """Join table: a team's ordered roster. `slot` (0-5) preserves order."""

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
