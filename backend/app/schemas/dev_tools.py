from typing import Literal

from pydantic import BaseModel

PokemonNumericField = Literal[
    "hp", "attack", "defense", "special_attack", "special_defense", "speed"
]
MoveNumericField = Literal["power", "accuracy", "pp", "priority", "effect_chance"]


class PokemonStatUpdate(BaseModel):
    """Dev-tool request body: directly overwrite one cached numeric stat,
    bypassing the ingestion/validation pipeline. Deliberately simulates
    "PokeAPI drifted from what's cached" so the scan's detection behavior
    can be demoed on demand rather than waiting for a real upstream change."""

    field: PokemonNumericField
    value: int


class MoveStatUpdate(BaseModel):
    field: MoveNumericField
    value: int


class MovepoolCorruption(BaseModel):
    """Dev-tool request body: add a move to a Pokemon's cached movepool that
    PokeAPI doesn't actually list for it. The next Pokemon scan re-fetches
    the real movepool, sees this move is missing from it, and treats it as
    "no longer learnable" — unassigning it from any team that has it
    equipped (if you've assigned it via the Team Builder in the meantime)
    and alerting the owner. This is how a real removed-move scenario is
    simulated, since there's no way to make PokeAPI itself drop a move on
    demand."""

    move_id: int
