import { useEffect, useState } from "react";
import { fetchTypeEffectiveness } from "../api/types";
import type { CatalogStatus } from "./usePokemonCatalog";

export interface TypeEffectivenessMap {
  data: Record<string, Record<string, number>>;
  status: CatalogStatus;
}

// Module-scoped, same reasoning as usePokemonMovepool: fetched once, lazily,
// only when the team details page actually mounts this hook, and shared if
// visited again later in the session rather than re-fetched per mount.
let cachedPromise: Promise<Record<string, Record<string, number>>> | null = null;

/** Lazily fetches the full {attacking_type: {defending_type: multiplier}}
 * chart — only the team details page needs it (to compute defense and
 * damage-dealt across up to 6 team members client-side), so it's not part
 * of any eagerly-fetched app-wide catalog. */
export function useTypeEffectiveness(): TypeEffectivenessMap {
  const [data, setData] = useState<Record<string, Record<string, number>>>({});
  const [status, setStatus] = useState<CatalogStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    if (!cachedPromise) {
      cachedPromise = fetchTypeEffectiveness();
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
