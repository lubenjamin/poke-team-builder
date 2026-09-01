import type { Move } from "./move";

export interface Pokemon {
  id: number;
  name: string;
  pokedex_number: number;
  is_default: boolean;
  is_battle_only: boolean;
  sprite_url: string;
  types: string[];
  hp: number;
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
}

export interface PokemonDetail extends Pokemon {
  learnable_moves: Move[];
  type_effectiveness: Record<string, number>;
}
