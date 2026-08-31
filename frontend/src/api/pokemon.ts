import { apiFetch } from "./client";
import type { Pokemon, PokemonDetail } from "../types/pokemon";

export function fetchAllPokemon(): Promise<Pokemon[]> {
  return apiFetch<Pokemon[]>("/api/pokemon", { withClientId: false });
}

/** Cheap freshness check for the client-side catalog cache — normalizes the
 * backend's `null` ("no changes detected yet") to "" so callers only ever
 * compare plain strings, never juggle a null case themselves. */
export async function fetchPokemonCatalogVersion(): Promise<string> {
  const result = await apiFetch<{ version: string | null }>("/api/pokemon/version", {
    withClientId: false,
  });
  return result.version ?? "";
}

/** {pokemon_id: learnable move ids} for the whole catalog — split out of
 * the main catalog fetch since only the team builder's move picker needs
 * it; see usePokemonMovepool for the lazy, cached fetch wrapper. */
export function fetchPokemonMovepool(): Promise<Record<number, number[]>> {
  return apiFetch<Record<number, number[]>>("/api/pokemon/movepool", { withClientId: false });
}

export function fetchPokemonDetail(idOrName: string): Promise<PokemonDetail> {
  return apiFetch<PokemonDetail>(`/api/pokemon/${idOrName}`, { withClientId: false });
}
