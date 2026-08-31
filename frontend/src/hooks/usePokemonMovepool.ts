import { useEffect, useState } from "react";
import { fetchPokemonMovepool } from "../api/pokemon";
import type { CatalogStatus } from "./usePokemonCatalog";

export interface PokemonMovepool {
  data: Record<number, number[]>;
  status: CatalogStatus;
}

// Module-scoped, not component state: the first RosterEditor to mount
// (Team Builder, Team Optimizer) triggers the fetch, and it's shared by any
// other instance mounted at the same time (Team Optimizer renders two) or
// mounted later in the session (switching between those pages) — without
// this, each mount/remount would re-fetch independently.
let cachedPromise: Promise<Record<number, number[]>> | null = null;

/** Lazily fetches {pokemon_id: learnable_move_ids[]} — only when a
 * team-builder-related page actually mounts this hook, unlike the main
 * Pokemon/move catalogs which fetch eagerly in App.tsx. This data used to
 * be bundled into every /api/pokemon response (paid by every page,
 * Pokedex included, even though only the move picker needs it); splitting
 * it out here means a Pokedex-only visit never fetches it at all. */
export function usePokemonMovepool(): PokemonMovepool {
  const [data, setData] = useState<Record<number, number[]>>({});
  const [status, setStatus] = useState<CatalogStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    if (!cachedPromise) {
      cachedPromise = fetchPokemonMovepool();
    }
    cachedPromise
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
        cachedPromise = null; // allow a retry on the next mount
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, status };
}
