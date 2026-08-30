from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pokemon import MoveRead, PokemonRead


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
    moves: list[MoveRead]


class TeamDetail(TeamRead):
    roster: list[TeamPokemonRead]


class RosterSlotInput(BaseModel):
    pokemon_id: int
    move_ids: list[int] = Field(default_factory=list, max_length=4)

    @field_validator("move_ids")
    @classmethod
    def no_duplicate_moves(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("move_ids must not contain duplicates")
        return value


class RosterReplace(BaseModel):
    slots: list[RosterSlotInput] = Field(max_length=6)

    @field_validator("slots")
    @classmethod
    def no_duplicate_pokemon(cls, value: list[RosterSlotInput]) -> list[RosterSlotInput]:
        pokemon_ids = [slot.pokemon_id for slot in value]
        if len(set(pokemon_ids)) != len(pokemon_ids):
            raise ValueError("a roster cannot contain the same pokemon_id twice")
        return value
