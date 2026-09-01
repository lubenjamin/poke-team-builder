from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Pokemon(Base):
    """
    Local cache of PokeAPI data. `id` is the PokeAPI id.
    One row per form/variety (e.g. Rotom-Wash is its own row) — `species_id` links
    forms of the same species together; the national dex number lives on
    PokemonSpecies, not here, since it's shared across a species' forms.
    """

    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sprite_url: Mapped[str] = mapped_column(String, nullable=False)
    types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    species_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon_species.id"), nullable=False, index=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    is_battle_only: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    attack: Mapped[int] = mapped_column(Integer, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, nullable=False)
    special_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    special_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)

    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    species: Mapped["PokemonSpecies"] = relationship()

    @property
    def pokedex_number(self) -> int:
        return self.species.national_dex_number
