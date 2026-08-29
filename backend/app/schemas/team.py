from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pokemon import PokemonRead


class TeamCreate(BaseModel):
    name: str
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str
    description: str | None = None


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TeamPokemonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slot: int
    pokemon: PokemonRead


class TeamDetail(TeamRead):
    roster: list[TeamPokemonRead]


class RosterReplace(BaseModel):
    pokemon_ids: list[int] = Field(max_length=6)

    @field_validator("pokemon_ids")
    @classmethod
    def no_duplicates(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("pokemon_ids must not contain duplicates")
        return value
