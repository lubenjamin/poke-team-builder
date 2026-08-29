from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PokemonSpecies(Base):
    """One row per national dex entry (from /pokedex/national). A species can have
    multiple `pokemon` forms/varieties (e.g. Rotom's 5 forms) that all share the
    same national_dex_number."""

    __tablename__ = "pokemon_species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    national_dex_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
