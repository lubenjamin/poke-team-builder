import { apiFetch } from "./client";
import type { Pokemon, PokemonDetail } from "../types/pokemon";

export function fetchAllPokemon(): Promise<Pokemon[]> {
  return apiFetch<Pokemon[]>("/api/pokemon", { withClientId: false });
}

export function fetchPokemonDetail(idOrName: string): Promise<PokemonDetail> {
  return apiFetch<PokemonDetail>(`/api/pokemon/${idOrName}`, { withClientId: false });
}
