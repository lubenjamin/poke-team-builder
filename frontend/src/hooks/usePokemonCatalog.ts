import { useEffect, useState } from "react";
import { fetchAllPokemon, fetchPokemonCatalogVersion } from "../api/pokemon";
import type { Pokemon } from "../types/pokemon";

export type CatalogStatus = "loading" | "error" | "ready";

export interface PokemonCatalog {
  pokemon: Pokemon[];
  status: CatalogStatus;
}

// The ":v2" suffix busts any cache written before is_battle_only was added
// to PokemonRead — GET /api/pokemon/version only changes when the scan job
// detects a real data change (see PokemonChangeLog), not when the API
// response *shape* changes server-side, so a stale cache under the old key
// would otherwise keep serving entries with is_battle_only silently
// undefined forever. Bump this suffix again any time PokemonRead's shape
// changes in a way a consumer depends on.
const CACHE_KEY = "poke-team-builder:pokemon-catalog:v2";
const CACHE_VERSION_KEY = "poke-team-builder:pokemon-catalog-version:v2";

function readCache(): { pokemon: Pokemon[]; version: string } | null {
  try {
    const rawVersion = localStorage.getItem(CACHE_VERSION_KEY);
    const rawCatalog = localStorage.getItem(CACHE_KEY);
    if (rawVersion === null || rawCatalog === null) return null;
    return { pokemon: JSON.parse(rawCatalog) as Pokemon[], version: rawVersion };
  } catch {
    return null; // corrupt/inaccessible storage — treat as no cache
  }
}

function writeCache(pokemon: Pokemon[], version: string): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(pokemon));
    localStorage.setItem(CACHE_VERSION_KEY, version);
  } catch {
    // Storage full/unavailable — caching is a perf optimization, not
    // required for correctness, so just skip it silently.
  }
}

/** Fetches the full Pokemon catalog (~1300 rows, ~800KB) and shares it via
 * props from App.tsx, same reasoning as before: every consumer (Pokedex
 * table, team-builder search, alert banner) shares one fetch instead of
 * each re-fetching on every mount.
 *
 * Now also cached in localStorage across page reloads, since that full
 * fetch is expensive (multi-second on a cold Neon connection) and the data
 * essentially never changes except when the scan job detects something. A
 * cached copy renders immediately (stale-while-revalidate) while a cheap
 * GET /api/pokemon/version check runs in the background; the full ~800KB
 * payload is only re-fetched if that version doesn't match what was
 * cached — see api/pokemon.ts. */
export function usePokemonCatalog(): PokemonCatalog {
  const [pokemon, setPokemon] = useState<Pokemon[]>([]);
  const [status, setStatus] = useState<CatalogStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    const cached = readCache();

    if (cached) {
      setPokemon(cached.pokemon);
      setStatus("ready");
    }

    async function refresh() {
      try {
        const serverVersion = await fetchPokemonCatalogVersion();
        if (cached && serverVersion === cached.version) {
          return; // cache is still fresh, nothing more to do
        }

        const data = await fetchAllPokemon();
        if (cancelled) return;
        setPokemon(data);
        setStatus("ready");
        writeCache(data, serverVersion);
      } catch {
        if (!cancelled && !cached) setStatus("error");
        // If we already showed cached data, a failed refresh just means we
        // keep showing what we had rather than surfacing an error.
      }
    }

    refresh();
    return () => {
      cancelled = true;
    };
  }, []);

  return { pokemon, status };
}
