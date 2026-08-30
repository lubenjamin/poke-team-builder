import type { Pokemon } from "./pokemon";

export interface Move {
  id: number;
  name: string;
  type: string;
  damage_class: string;
  power: number | null;
  accuracy: number | null;
  pp: number | null;
  priority: number;
  effect_chance: number | null;
  effect_text: string | null;
}

export interface MoveDetail extends Move {
  learnable_by: Pokemon[];
}
