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
