export interface Pokemon {
  id: number;
  name: string;
  pokedex_number: number;
  is_default: boolean;
  sprite_url: string;
  types: string[];
  hp: number;
  attack: number;
  defense: number;
  special_attack: number;
  special_defense: number;
  speed: number;
}
