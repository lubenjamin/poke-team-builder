import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchChanges, fetchMoveChanges } from "../api/changes";
import { DamageClassIcon } from "../components/DamageClassIcon";
import { PageHero } from "../components/PageHero";
import { typeColor } from "../components/typeColors";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { ChangeLogEntry, MoveChangeLogEntry } from "../types/changeLog";
import "./ChangeLogPage.css";

interface ChangeLogPageProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

type Kind = "pokemon" | "move";
type Filter = "all" | Kind;

interface MergedEntry {
  kind: Kind;
  key: string;
  entityId: number;
  field_name: string;
  old_value: string;
  new_value: string;
  detected_at: string;
}

function mergeEntries(
  pokemonChanges: ChangeLogEntry[],
  moveChanges: MoveChangeLogEntry[],
): MergedEntry[] {
  const merged: MergedEntry[] = [
    ...pokemonChanges.map((c) => ({
      kind: "pokemon" as const,
      key: `pokemon-${c.id}`,
      entityId: c.pokemon_id,
      field_name: c.field_name,
      old_value: c.old_value,
      new_value: c.new_value,
      detected_at: c.detected_at,
    })),
    ...moveChanges.map((c) => ({
      kind: "move" as const,
      key: `move-${c.id}`,
      entityId: c.move_id,
      field_name: c.field_name,
      old_value: c.old_value,
      new_value: c.new_value,
      detected_at: c.detected_at,
    })),
  ];
  return merged.sort((a, b) => b.detected_at.localeCompare(a.detected_at));
}

export function ChangeLogPage({ catalog, moveCatalog }: ChangeLogPageProps) {
  useDocumentTitle("Change Log");
  const [entries, setEntries] = useState<MergedEntry[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchChanges(), fetchMoveChanges()])
      .then(([pokemonChanges, moveChanges]) => {
        if (cancelled) return;
        setEntries(mergeEntries(pokemonChanges, moveChanges));
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = filter === "all" ? entries : entries.filter((e) => e.kind === filter);
  const pokemonCount = entries.filter((e) => e.kind === "pokemon").length;
  const moveCount = entries.filter((e) => e.kind === "move").length;

  return (
    <main>
      <PageHero
        title="Change Log"
        description="Recently detected changes to Pokémon and move data, found by the recurring scan jobs that re-check PokeAPI."
      />

      {status === "ready" && entries.length > 0 && (
        <div className="change-log__filters">
          <button
            type="button"
            className={`change-log__filter-btn${filter === "all" ? " change-log__filter-btn--active" : ""}`}
            onClick={() => setFilter("all")}
          >
            All ({entries.length})
          </button>
          <button
            type="button"
            className={`change-log__filter-btn${filter === "pokemon" ? " change-log__filter-btn--active" : ""}`}
            onClick={() => setFilter("pokemon")}
          >
            Pokémon ({pokemonCount})
          </button>
          <button
            type="button"
            className={`change-log__filter-btn${filter === "move" ? " change-log__filter-btn--active" : ""}`}
            onClick={() => setFilter("move")}
          >
            Moves ({moveCount})
          </button>
        </div>
      )}

      {status === "loading" && <p className="change-log__message">Loading change log...</p>}
      {status === "error" && (
        <p className="change-log__message">
          Couldn't load the change log. Is the backend running?
        </p>
      )}
      {status === "ready" && entries.length === 0 && (
        <p className="change-log__message">No changes detected yet.</p>
      )}

      {status === "ready" && filtered.length > 0 && (
        <ul className="change-log__list">
          {filtered.map((entry) => (
            <li className="change-log__row" key={entry.key}>
              {entry.kind === "pokemon" ? (
                <PokemonCell pokemonId={entry.entityId} catalog={catalog} />
              ) : (
                <MoveCell moveId={entry.entityId} moveCatalog={moveCatalog} />
              )}
              <span className="change-log__field">{entry.field_name.replace(/_/g, " ")}</span>
              <span className="change-log__diff">
                <span className="change-log__old">{entry.old_value}</span>
                <span className="change-log__arrow">→</span>
                <span className="change-log__new">{entry.new_value}</span>
              </span>
              <span className="change-log__timestamp">
                {new Date(entry.detected_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function PokemonCell({ pokemonId, catalog }: { pokemonId: number; catalog: PokemonCatalog }) {
  const pokemon = catalog.pokemon.find((p) => p.id === pokemonId);
  if (!pokemon) {
    return (
      <span className="change-log__entity change-log__entity--unknown">
        Pokémon #{pokemonId}
      </span>
    );
  }
  return (
    <Link to={`/pokemon/${pokemon.name}`} className="change-log__entity">
      <img src={pokemon.sprite_url} alt={pokemon.name} />
      <span>{pokemon.name.replace(/-/g, " ")}</span>
    </Link>
  );
}

function MoveCell({ moveId, moveCatalog }: { moveId: number; moveCatalog: MoveCatalog }) {
  const move = moveCatalog.moves.find((m) => m.id === moveId);
  if (!move) {
    return <span className="change-log__entity change-log__entity--unknown">Move #{moveId}</span>;
  }
  return (
    <Link to={`/moves/${move.name}`} className="change-log__entity">
      <span
        className="change-log__move-type-badge"
        style={{ backgroundColor: typeColor(move.type) }}
      >
        {move.type}
      </span>
      <DamageClassIcon damageClass={move.damage_class} size={16} />
      <span>{move.name.replace(/-/g, " ")}</span>
    </Link>
  );
}
