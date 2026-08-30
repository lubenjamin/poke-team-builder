import { useEffect, useMemo, useRef, useState } from "react";
import type { CatalogStatus } from "../hooks/useMoveCatalog";
import type { Move } from "../types/move";
import type { Pokemon } from "../types/pokemon";
import { matchesSearch } from "../utils/search";
import { DamageClassIcon } from "./DamageClassIcon";
import "./MovePicker.css";
import { typeColor } from "./typeColors";

interface MovePickerProps {
  pokemon: Pokemon;
  /** id -> Move, built once from the already-fetched move catalog (see
   * RosterEditor) so opening the picker never costs a network round trip —
   * resolving a Pokemon's learnable moves is a synchronous lookup against
   * data the app already has in memory. */
  moveById: Map<number, Move>;
  moveCatalogStatus: CatalogStatus;
  excludeIds: number[];
  onAdd: (move: Move) => void;
  onClose: () => void;
}

/** Same inline-search-in-place pattern as PokemonPicker, but scoped to one
 * Pokemon's actual movepool — resolved client-side from `pokemon.learnable_move_ids`
 * against the shared move catalog, rather than fetching per Pokemon on open. */
export function MovePicker({
  pokemon,
  moveById,
  moveCatalogStatus,
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
    for (const moveId of pokemon.learnable_move_ids) {
      const move = moveById.get(moveId);
      if (move) moves.push(move);
    }
    return moves.sort((a, b) => a.name.localeCompare(b.name));
  }, [pokemon.learnable_move_ids, moveById]);

  const results = useMemo(() => {
    const excluded = new Set(excludeIds);
    return learnableMoves.filter((m) => !excluded.has(m.id) && matchesSearch(m.name, query));
  }, [learnableMoves, query, excludeIds]);

  const ready = moveCatalogStatus === "ready";

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
      {moveCatalogStatus === "error" && (
        <div className="move-picker__empty">Couldn't load moves</div>
      )}
    </div>
  );
}
