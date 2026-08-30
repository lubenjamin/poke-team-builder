import { useEffect, useState } from "react";
import { fetchAllMoves } from "../api/moves";
import type { Move } from "../types/move";

export type CatalogStatus = "loading" | "error" | "ready";

export interface MoveCatalog {
  moves: Move[];
  status: CatalogStatus;
}

/** Fetches the full move catalog once per app session, same reasoning as
 * usePokemonCatalog — call this in App.tsx and pass the result down, so the
 * move catalog page and the team builder's move picker share one fetch
 * instead of each re-fetching on every mount. */
export function useMoveCatalog(): MoveCatalog {
  const [moves, setMoves] = useState<Move[]>([]);
  const [status, setStatus] = useState<CatalogStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    fetchAllMoves()
      .then((data) => {
        if (cancelled) return;
        setMoves(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { moves, status };
}
