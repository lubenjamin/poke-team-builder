import { useMemo, useState } from "react";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Pokemon } from "../types/pokemon";
import { FilterSection, FilterTray } from "./FilterTray";
import { TypeFilter } from "./TypeFilter";
import { typeColor } from "./typeColors";
import "./PokedexTable.css";

const PAGE_SIZE = 50;

type SortField =
  | "pokedex_number"
  | "name"
  | "types"
  | "hp"
  | "attack"
  | "defense"
  | "special_attack"
  | "special_defense"
  | "speed"
  | "bst";

type SortDir = "asc" | "desc";

const COLUMNS: { field: SortField; label: string }[] = [
  { field: "name", label: "Name" },
  { field: "types", label: "Type" },
  { field: "hp", label: "HP" },
  { field: "attack", label: "ATK" },
  { field: "defense", label: "DEF" },
  { field: "special_attack", label: "SPA" },
  { field: "special_defense", label: "SPD" },
  { field: "speed", label: "SPE" },
  { field: "bst", label: "BST" },
];

function bst(p: Pokemon): number {
  return p.hp + p.attack + p.defense + p.special_attack + p.special_defense + p.speed;
}

function sortValue(p: Pokemon, field: SortField): string | number {
  if (field === "bst") return bst(p);
  if (field === "types") return p.types.join("/");
  return p[field];
}

interface PokedexTableProps {
  catalog: PokemonCatalog;
}

export function PokedexTable({ catalog }: PokedexTableProps) {
  const { pokemon, status } = catalog;

  const [query, setQuery] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>("pokedex_number");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return pokemon.filter((p) => {
      if (q && !p.name.toLowerCase().includes(q)) return false;
      if (selectedTypes.size > 0 && !p.types.some((t) => selectedTypes.has(t))) return false;
      return true;
    });
  }, [pokemon, query, selectedTypes]);

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const va = sortValue(a, sortField);
      const vb = sortValue(b, sortField);
      if (typeof va === "string" || typeof vb === "string") {
        return dir * String(va).localeCompare(String(vb));
      }
      return dir * (va - vb);
    });
  }, [filtered, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = sorted.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  function handleSort(field: SortField) {
    if (field === sortField) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  }

  function toggleType(type: string) {
    setPage(1);
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  if (status === "loading") return <p className="pokedex__message">Loading Pokémon...</p>;
  if (status === "error") {
    return <p className="pokedex__message">Couldn't load Pokémon. Is the backend running?</p>;
  }

  return (
    <div className="pokedex">
      <div className="pokedex__filters">
        <input
          type="search"
          className="pokedex__search"
          placeholder="Search by name..."
          value={query}
          onChange={(e) => {
            setPage(1);
            setQuery(e.target.value);
          }}
        />
        <button
          type="button"
          className="pokedex__filter-btn"
          onClick={() => setFiltersOpen(true)}
          aria-label="Open filters"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M1 2h14l-5.2 6.2v4.8l-3.6 1.8V8.2L1 2z"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>
          Filters
          {selectedTypes.size > 0 && <span className="pokedex__filter-badge">{selectedTypes.size}</span>}
        </button>
        <span className="pokedex__count">{sorted.length} Pokémon</span>
      </div>

      <FilterTray open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <FilterSection title="Type">
          <TypeFilter
            selected={selectedTypes}
            onToggle={toggleType}
            onClear={() => {
              setPage(1);
              setSelectedTypes(new Set());
            }}
          />
        </FilterSection>
      </FilterTray>

      <div className="pokedex__table-wrap">
        <table className="pokedex__table">
          <thead>
            <tr>
              <th>
                <button type="button" className="pokedex__sort-btn" onClick={() => handleSort("pokedex_number")}>
                  #{sortField === "pokedex_number" && <span className="pokedex__sort-arrow">{sortDir === "asc" ? "▲" : "▼"}</span>}
                </button>
              </th>
              <th aria-hidden="true" />
              {COLUMNS.map(({ field, label }) => (
                <th key={field}>
                  <button type="button" className="pokedex__sort-btn" onClick={() => handleSort(field)}>
                    {label}
                    {sortField === field && <span className="pokedex__sort-arrow">{sortDir === "asc" ? "▲" : "▼"}</span>}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageItems.map((p) => (
              <tr key={p.id}>
                <td className="pokedex__dim">{p.pokedex_number}</td>
                <td className="pokedex__sprite-cell">
                  <img src={p.sprite_url} alt={p.name} loading="lazy" />
                </td>
                <td className="pokedex__name">{p.name.replace(/-/g, " ")}</td>
                <td>
                  <div className="pokedex__types">
                    {p.types.map((t) => (
                      <span key={t} className="pokedex__type-badge" style={{ backgroundColor: typeColor(t) }}>
                        {t}
                      </span>
                    ))}
                  </div>
                </td>
                <td>{p.hp}</td>
                <td>{p.attack}</td>
                <td>{p.defense}</td>
                <td>{p.special_attack}</td>
                <td>{p.special_defense}</td>
                <td>{p.speed}</td>
                <td className="pokedex__bst">{bst(p)}</td>
              </tr>
            ))}
            {pageItems.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 2} className="pokedex__message">
                  No Pokémon match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pokedex__pagination">
        <button type="button" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>
          Previous
        </button>
        <span>
          Page {currentPage} of {totalPages}
        </span>
        <button type="button" disabled={currentPage >= totalPages} onClick={() => setPage(currentPage + 1)}>
          Next
        </button>
      </div>
    </div>
  );
}
