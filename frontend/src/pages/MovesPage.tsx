import { useMemo, useState } from "react";
import { FilterSection, FilterTray } from "../components/FilterTray";
import { MoveCard } from "../components/MoveCard";
import { PageHero } from "../components/PageHero";
import { TypeFilter } from "../components/TypeFilter";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import { matchesSearch } from "../utils/search";
import "./MovesPage.css";

interface MovesPageProps {
  catalog: MoveCatalog;
}

export function MovesPage({ catalog }: MovesPageProps) {
  useDocumentTitle("Moves");
  const { moves, status } = catalog;

  const [query, setQuery] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [filtersOpen, setFiltersOpen] = useState(false);

  const filtered = useMemo(() => {
    return moves.filter((m) => {
      if (!matchesSearch(m.name, query)) return false;
      if (selectedTypes.size > 0 && !selectedTypes.has(m.type)) return false;
      return true;
    });
  }, [moves, query, selectedTypes]);

  function toggleType(type: string) {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  return (
    <main>
      <PageHero
        title="Moves"
        description="Every move in the game — type, damage class, power, accuracy, PP, and effect. Search by name or filter by type."
      />

      <div className="moves-page__filters">
        <input
          type="search"
          className="moves-page__search"
          placeholder="Search by name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="button"
          className="moves-page__filter-btn"
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
          {selectedTypes.size > 0 && (
            <span className="moves-page__filter-badge">{selectedTypes.size}</span>
          )}
        </button>
        <span className="moves-page__count">{filtered.length} Moves</span>
      </div>

      <FilterTray open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <FilterSection title="Type">
          <TypeFilter
            selected={selectedTypes}
            onToggle={toggleType}
            onClear={() => setSelectedTypes(new Set())}
          />
        </FilterSection>
      </FilterTray>

      {status === "loading" && <p className="moves-page__message">Loading moves...</p>}
      {status === "error" && (
        <p className="moves-page__message">Couldn't load moves. Is the backend running?</p>
      )}
      {status === "ready" && (
        <div className="moves-page__grid">
          {filtered.map((move) => (
            <MoveCard key={move.id} move={move} />
          ))}
          {filtered.length === 0 && (
            <p className="moves-page__message">No moves match your filters.</p>
          )}
        </div>
      )}
    </main>
  );
}
