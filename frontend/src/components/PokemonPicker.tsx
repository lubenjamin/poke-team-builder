import { useEffect, useMemo, useRef, useState } from "react";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Pokemon } from "../types/pokemon";
import { typeColor } from "./typeColors";
import "./PokemonPicker.css";

interface PokemonPickerProps {
  catalog: PokemonCatalog;
  excludeIds: number[];
  onAdd: (pokemon: Pokemon) => void;
  onClose: () => void;
}

/** Renders inline in place of the empty slot that triggered it — see
 * TeamBuilder.tsx, which mounts this only for the currently "searching" slot. */
export function PokemonPicker({ catalog, excludeIds, onAdd, onClose }: PokemonPickerProps) {
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

  const alphabetical = useMemo(
    () => [...catalog.pokemon].sort((a, b) => a.name.localeCompare(b.name)),
    [catalog.pokemon],
  );

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const excluded = new Set(excludeIds);
    return alphabetical.filter(
      (p) => !excluded.has(p.id) && (!q || p.name.toLowerCase().includes(q)),
    );
  }, [alphabetical, query, excludeIds]);

  return (
    <div
      className="pokemon-picker pokemon-picker--inline"
      ref={containerRef}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <input
        ref={inputRef}
        type="search"
        className="pokemon-picker__search"
        placeholder="Search Pokémon..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {results.length > 0 && (
        <ul className="pokemon-picker__results">
          {results.map((p) => (
            <li key={p.id}>
              <button type="button" className="pokemon-picker__result" onClick={() => onAdd(p)}>
                <img src={p.sprite_url} alt={p.name} loading="lazy" />
                <span className="pokemon-picker__name">{p.name.replace(/-/g, " ")}</span>
                <div className="pokemon-picker__types">
                  {p.types.map((t) => (
                    <span
                      key={t}
                      className="pokemon-picker__type-badge"
                      style={{ backgroundColor: typeColor(t) }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
      {results.length === 0 && <div className="pokemon-picker__empty">No matches</div>}
    </div>
  );
}
