import type { Pokemon } from "./pokemon";

export interface Team {
  id: number;
  client_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamPokemonSlot {
  slot: number;
  pokemon: Pokemon;
}

export interface TeamDetail extends Team {
  roster: TeamPokemonSlot[];
}
