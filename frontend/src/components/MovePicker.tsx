import { useEffect, useMemo, useRef, useState } from "react";
import { fetchPokemonDetail } from "../api/pokemon";
import type { Move } from "../types/move";
import { DamageClassIcon } from "./DamageClassIcon";
import "./MovePicker.css";
import { typeColor } from "./typeColors";

interface MovePickerProps {
  pokemonId: number;
  excludeIds: number[];
  onAdd: (move: Move) => void;
  onClose: () => void;
}

/** Same inline-search-in-place pattern as PokemonPicker, but scoped to one
 * Pokemon's actual movepool (fetched on open) rather than the whole catalog —
 * a Pokemon can only be taught moves it can actually learn. */
export function MovePicker({ pokemonId, excludeIds, onAdd, onClose }: MovePickerProps) {
  const [learnableMoves, setLearnableMoves] = useState<Move[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchPokemonDetail(String(pokemonId))
      .then((data) => {
        if (cancelled) return;
        setLearnableMoves([...data.learnable_moves].sort((a, b) => a.name.localeCompare(b.name)));
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [pokemonId]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const excluded = new Set(excludeIds);
    return learnableMoves.filter(
      (m) => !excluded.has(m.id) && (!q || m.name.toLowerCase().includes(q)),
    );
  }, [learnableMoves, query, excludeIds]);

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
        placeholder={status === "loading" ? "Loading moves..." : "Search moves..."}
        value={query}
        disabled={status !== "ready"}
        onChange={(e) => setQuery(e.target.value)}
      />
      {status === "ready" && results.length > 0 && (
        <ul className="move-picker__results">
          {results.map((m) => (
            <li key={m.id}>
              <button type="button" className="move-picker__result" onClick={() => onAdd(m)}>
                <span className="move-picker__name">{m.name.replace(/-/g, " ")}</span>
                <span
                  className="move-picker__type-badge"
                  style={{ backgroundColor: typeColor(m.type) }}
                >
                  {m.type}
                </span>
                <DamageClassIcon damageClass={m.damage_class} size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {status === "ready" && results.length === 0 && (
        <div className="move-picker__empty">No matches</div>
      )}
      {status === "error" && <div className="move-picker__empty">Couldn't load moves</div>}
    </div>
  );
}
