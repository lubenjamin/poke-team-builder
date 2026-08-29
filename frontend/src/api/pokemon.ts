import { apiFetch } from "./client";
import type { Pokemon } from "../types/pokemon";

export function fetchAllPokemon(): Promise<Pokemon[]> {
  return apiFetch<Pokemon[]>("/api/pokemon", { withClientId: false });
}
