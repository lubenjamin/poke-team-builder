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


def _check_no_duplicate_pokemon(slots: list[RosterSlotInput]) -> list[RosterSlotInput]:
    pokemon_ids = [slot.pokemon_id for slot in slots]
    if len(set(pokemon_ids)) != len(pokemon_ids):
        raise ValueError("a roster cannot contain the same pokemon_id twice")
    return slots


class RosterReplace(BaseModel):
    slots: list[RosterSlotInput] = Field(max_length=6)

    @field_validator("slots")
    @classmethod
    def no_duplicate_pokemon(cls, value: list[RosterSlotInput]) -> list[RosterSlotInput]:
        return _check_no_duplicate_pokemon(value)


class CounterTeamRequest(BaseModel):
    """The opponent's team, submitted to generate a counter team against.
    Unlike RosterReplace (which allows saving an empty roster), this requires
    at least one Pokemon — there's nothing to counter otherwise."""

    slots: list[RosterSlotInput] = Field(min_length=1, max_length=6)

    @field_validator("slots")
    @classmethod
    def no_duplicate_pokemon(cls, value: list[RosterSlotInput]) -> list[RosterSlotInput]:
        return _check_no_duplicate_pokemon(value)
