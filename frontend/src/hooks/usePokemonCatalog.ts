import { useEffect, useState } from "react";
import { fetchAllPokemon } from "../api/pokemon";
import type { Pokemon } from "../types/pokemon";

export type CatalogStatus = "loading" | "error" | "ready";

export interface PokemonCatalog {
  pokemon: Pokemon[];
  status: CatalogStatus;
}

/** Fetches the full Pokemon catalog once per app session. Call this in App.tsx
 * and pass the result down as props — it's ~1300 rows and doesn't change within
 * a session, so every consumer (the Pokedex table, the team-builder search)
 * should share one fetch instead of each re-fetching on every mount. */
export function usePokemonCatalog(): PokemonCatalog {
  const [pokemon, setPokemon] = useState<Pokemon[]>([]);
  const [status, setStatus] = useState<CatalogStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    fetchAllPokemon()
      .then((data) => {
        if (cancelled) return;
        setPokemon(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { pokemon, status };
}
