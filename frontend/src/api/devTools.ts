import { apiFetch } from "./client";
import type { ScanResult } from "../types/scan";

export type PokemonNumericField =
  | "hp"
  | "attack"
  | "defense"
  | "special_attack"
  | "special_defense"
  | "speed";

export type MoveNumericField = "power" | "accuracy" | "pp" | "priority" | "effect_chance";

export const POKEMON_NUMERIC_FIELDS: PokemonNumericField[] = [
  "hp",
  "attack",
  "defense",
  "special_attack",
  "special_defense",
  "speed",
];

export const MOVE_NUMERIC_FIELDS: MoveNumericField[] = [
  "power",
  "accuracy",
  "pp",
  "priority",
  "effect_chance",
];

export function scanPokemon(limit?: number): Promise<ScanResult> {
  const query = limit != null ? `?limit=${limit}` : "";
  return apiFetch<ScanResult>(`/api/internal/scan-pokemon${query}`, {
    method: "POST",
    withClientId: false,
    withInternalSecret: true,
  });
}

export function scanMoves(limit?: number): Promise<ScanResult> {
  const query = limit != null ? `?limit=${limit}` : "";
  return apiFetch<ScanResult>(`/api/internal/scan-moves${query}`, {
    method: "POST",
    withClientId: false,
    withInternalSecret: true,
  });
}

export function corruptPokemonStat(
  pokemonId: number,
  field: PokemonNumericField,
  value: number,
): Promise<void> {
  return apiFetch<void>(`/api/internal/pokemon/${pokemonId}`, {
    method: "PATCH",
    body: { field, value },
    withClientId: false,
    withInternalSecret: true,
  });
}

export function corruptMoveStat(
  moveId: number,
  field: MoveNumericField,
  value: number,
): Promise<void> {
  return apiFetch<void>(`/api/internal/moves/${moveId}`, {
    method: "PATCH",
    body: { field, value },
    withClientId: false,
    withInternalSecret: true,
  });
}

/** Adds a move to a Pokemon's cached movepool that PokeAPI doesn't actually
 * list for it — the next Pokemon scan sees it's missing from the real
 * movepool and treats it as "no longer learnable" (unassigning it from any
 * team that has it equipped, and alerting the owner). This is how a
 * removed-move scenario gets simulated on demand. */
export function corruptPokemonMovepool(pokemonId: number, moveId: number): Promise<void> {
  return apiFetch<void>(`/api/internal/pokemon/${pokemonId}/movepool`, {
    method: "POST",
    body: { move_id: moveId },
    withClientId: false,
    withInternalSecret: true,
  });
}
