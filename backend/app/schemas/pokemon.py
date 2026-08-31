from pydantic import BaseModel, ConfigDict


class PokemonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    pokedex_number: int
    is_default: bool
    sprite_url: str
    types: list[str]
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


class MoveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    damage_class: str
    power: int | None
    accuracy: int | None
    pp: int | None
    priority: int
    effect_chance: int | None
    effect_text: str | None


class PokemonDetail(PokemonRead):
    learnable_moves: list[MoveRead]
    type_effectiveness: dict[str, float]


class PokemonCatalogVersion(BaseModel):
    version: str | None
