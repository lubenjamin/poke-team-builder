import { useEffect, useMemo, useRef, useState } from "react";
import type { CatalogStatus } from "../hooks/useMoveCatalog";
import type { Move } from "../types/move";
import { matchesSearch } from "../utils/search";
import { DamageClassIcon } from "./DamageClassIcon";
import "./MovePicker.css";
import { typeColor } from "./typeColors";

interface MovePickerProps {
  /** This Pokemon's learnable move ids, from usePokemonMovepool (see
   * RosterEditor) — fetched lazily/once and shared across the session, so
   * opening the picker never costs a per-open network round trip. */
  learnableMoveIds: number[];
  /** id -> Move, built once from the already-fetched move catalog. */
  moveById: Map<number, Move>;
  moveCatalogStatus: CatalogStatus;
  /** Status of the learnableMoveIds fetch itself — both this and the move
   * catalog need to be ready before results can be trusted. */
  movepoolStatus: CatalogStatus;
  excludeIds: number[];
  onAdd: (move: Move) => void;
  onClose: () => void;
}

/** Same inline-search-in-place pattern as PokemonPicker, but scoped to one
 * Pokemon's actual movepool — resolved client-side from the already-fetched
 * movepool map and move catalog, rather than fetching per Pokemon on open. */
export function MovePicker({
  learnableMoveIds,
  moveById,
  moveCatalogStatus,
  movepoolStatus,
  excludeIds,
  onAdd,
  onClose,
}: MovePickerProps) {
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const learnableMoves = useMemo(() => {
    const moves: Move[] = [];
    for (const moveId of learnableMoveIds) {
      const move = moveById.get(moveId);
      if (move) moves.push(move);
    }
    return moves.sort((a, b) => a.name.localeCompare(b.name));
  }, [learnableMoveIds, moveById]);

  const results = useMemo(() => {
    const excluded = new Set(excludeIds);
    return learnableMoves.filter((m) => !excluded.has(m.id) && matchesSearch(m.name, query));
  }, [learnableMoves, query, excludeIds]);

  const ready = moveCatalogStatus === "ready" && movepoolStatus === "ready";
  const errored = moveCatalogStatus === "error" || movepoolStatus === "error";

  return (
    <div
      className="move-picker"
      ref={containerRef}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <input
        ref={inputRef}
        type="search"
        className="move-picker__search"
        placeholder={ready ? "Search moves..." : "Loading moves..."}
        value={query}
        disabled={!ready}
        onChange={(e) => setQuery(e.target.value)}
      />
      {ready && results.length > 0 && (
        <ul className="move-picker__results">
          {results.map((m) => (
            <li key={m.id}>
              <button type="button" className="move-picker__result" onClick={() => onAdd(m)}>
                <span className="move-picker__name">{m.name.replace(/-/g, " ")}</span>
                <span className="move-picker__meta">
                  <span
                    className="move-picker__type-badge"
                    style={{ backgroundColor: typeColor(m.type) }}
                  >
                    {m.type}
                  </span>
                  <span className="move-picker__damage-class">
                    <DamageClassIcon damageClass={m.damage_class} size={13} />
                    {m.damage_class}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {ready && results.length === 0 && <div className="move-picker__empty">No matches</div>}
      {errored && <div className="move-picker__empty">Couldn't load moves</div>}
    </div>
  );
}
