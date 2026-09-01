export interface VgcWorldsMove {
  display_name: string;
  resolved_id: number | null;
  type: string | null;
  damage_class: string | null;
}

export interface VgcWorldsPokemon {
  slug: string;
  display_name: string;
  item: string;
  ability: string;
  nature: string;
  moves: VgcWorldsMove[];
  resolved_id: number | null;
  sprite_url: string | null;
  types: string[] | null;
}

export interface VgcWorldsEntry {
  rank: number;
  placement: string;
  player_name: string;
  country: string;
  pokemon: VgcWorldsPokemon[];
}
