import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import { createTeam, fetchTeam, replaceRoster, updateTeam } from "../api/teams";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Move } from "../types/move";
import type { Pokemon } from "../types/pokemon";
import type { Team } from "../types/team";
import { DamageClassIcon } from "./DamageClassIcon";
import { MovePicker } from "./MovePicker";
import { PokemonPicker } from "./PokemonPicker";
import "./TeamBuilder.css";
import { typeColor } from "./typeColors";

const MAX_ROSTER_SIZE = 6;
const MAX_MOVES_PER_POKEMON = 4;
const NAME_MAX_LENGTH = 40;
const DESCRIPTION_MAX_LENGTH = 2500;

interface RosterSlotState {
  pokemon: Pokemon;
  moves: Move[];
}

interface MoveSearchTarget {
  rosterIndex: number;
  moveSlotIndex: number;
}

interface TeamBuilderProps {
  teamId: number | null; // null = new, unsaved team
  catalog: PokemonCatalog;
  onSaved: (team: Team) => void;
  onDirtyChange: (dirty: boolean) => void;
}

function snapshotRoster(roster: RosterSlotState[]): string {
  return JSON.stringify(
    roster.map((r) => ({ pokemonId: r.pokemon.id, moveIds: r.moves.map((m) => m.id) })),
  );
}

export function TeamBuilder({ teamId, catalog, onSaved, onDirtyChange }: TeamBuilderProps) {
  const [status, setStatus] = useState<"loading" | "error" | "ready">(
    teamId === null ? "ready" : "loading",
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [roster, setRoster] = useState<RosterSlotState[]>([]);
  const [savedName, setSavedName] = useState("");
  const [savedDescription, setSavedDescription] = useState("");
  const [savedRosterSnapshot, setSavedRosterSnapshot] = useState("[]");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [searchSlotIndex, setSearchSlotIndex] = useState<number | null>(null);
  const [moveSearchTarget, setMoveSearchTarget] = useState<MoveSearchTarget | null>(null);

  useEffect(() => {
    if (teamId === null) {
      setName("");
      setDescription("");
      setRoster([]);
      setSavedName("");
      setSavedDescription("");
      setSavedRosterSnapshot("[]");
      setStatus("ready");
      return;
    }
    let cancelled = false;
    setStatus("loading");
    fetchTeam(teamId)
      .then((data) => {
        if (cancelled) return;
        const hydrated: RosterSlotState[] = data.roster.map((r) => ({
          pokemon: r.pokemon,
          moves: r.moves,
        }));
        setName(data.name);
        setDescription(data.description ?? "");
        setRoster(hydrated);
        setSavedName(data.name);
        setSavedDescription(data.description ?? "");
        setSavedRosterSnapshot(snapshotRoster(hydrated));
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [teamId]);

  const currentIds = roster.map((r) => r.pokemon.id);
  const isDirty =
    name !== savedName ||
    description !== savedDescription ||
    snapshotRoster(roster) !== savedRosterSnapshot;

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

  function handleAdd(pokemon: Pokemon) {
    if (roster.length >= MAX_ROSTER_SIZE || currentIds.includes(pokemon.id)) return;
    setRoster((prev) => [...prev, { pokemon, moves: [] }]);
    setSearchSlotIndex(null);
  }

  function handleRemove(index: number) {
    setRoster((prev) => prev.filter((_, i) => i !== index));
  }

  function handleDragOverSlot(targetIndex: number) {
    if (draggedId === null) return;
    setRoster((prev) => {
      const currentIndex = prev.findIndex((r) => r.pokemon.id === draggedId);
      if (currentIndex === -1 || currentIndex === targetIndex) return prev;
      const next = [...prev];
      const [moved] = next.splice(currentIndex, 1);
      next.splice(targetIndex, 0, moved);
      return next;
    });
  }

  function handleAddMove(rosterIndex: number, move: Move) {
    setRoster((prev) => {
      const slot = prev[rosterIndex];
      if (slot.moves.length >= MAX_MOVES_PER_POKEMON || slot.moves.some((m) => m.id === move.id)) {
        return prev;
      }
      const next = [...prev];
      next[rosterIndex] = { ...slot, moves: [...slot.moves, move] };
      return next;
    });
    setMoveSearchTarget(null);
  }

  function handleRemoveMove(rosterIndex: number, moveId: number) {
    setRoster((prev) => {
      const slot = prev[rosterIndex];
      const next = [...prev];
      next[rosterIndex] = { ...slot, moves: slot.moves.filter((m) => m.id !== moveId) };
      return next;
    });
  }

  async function handleSave() {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Team needs a name");
      return;
    }
    const trimmedDescription = description.trim() || null;
    setSaving(true);
    setError(null);
    try {
      let id = teamId;
      if (id === null) {
        const created = await createTeam(trimmedName, trimmedDescription);
        id = created.id;
      } else if (trimmedName !== savedName || description !== savedDescription) {
        await updateTeam(id, trimmedName, trimmedDescription);
      }
      const updated = await replaceRoster(
        id,
        roster.map((r) => ({ pokemon_id: r.pokemon.id, move_ids: r.moves.map((m) => m.id) })),
      );
      const hydrated: RosterSlotState[] = updated.roster.map((r) => ({
        pokemon: r.pokemon,
        moves: r.moves,
      }));
      setName(updated.name);
      setDescription(updated.description ?? "");
      setRoster(hydrated);
      setSavedName(updated.name);
      setSavedDescription(updated.description ?? "");
      setSavedRosterSnapshot(snapshotRoster(hydrated));
      onSaved(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save team");
    } finally {
      setSaving(false);
    }
  }

  if (status === "loading") return <p className="team-builder__message">Loading team...</p>;
  if (status === "error") return <p className="team-builder__message">Couldn't load this team.</p>;

  return (
    <div className="team-builder">
      <div className="team-builder__details-card">
        <div className="team-builder__details-header">
          <h2>Team Details</h2>
          <span className="team-builder__count">
            {roster.length}/{MAX_ROSTER_SIZE}
          </span>
        </div>

        <label className="team-builder__field">
          <span className="team-builder__field-label">
            Name
            <span className="team-builder__char-count">
              {name.length}/{NAME_MAX_LENGTH}
            </span>
          </span>
          <input
            className="team-builder__name-input"
            value={name}
            maxLength={NAME_MAX_LENGTH}
            placeholder="e.g. Rain Offense"
            onChange={(e) => setName(e.target.value)}
          />
        </label>

        <label className="team-builder__field">
          <span className="team-builder__field-label">
            Description <span className="team-builder__field-optional">(optional)</span>
            <span className="team-builder__char-count">
              {description.length}/{DESCRIPTION_MAX_LENGTH}
            </span>
          </span>
          <textarea
            className="team-builder__description-input"
            value={description}
            maxLength={DESCRIPTION_MAX_LENGTH}
            placeholder="Notes on the gameplan, leads, and counters..."
            rows={3}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>

        <div className="team-builder__field">
          <span className="team-builder__field-label">Pokémon &amp; Moves</span>
          <ol className="team-builder__roster">
            {roster.map((slotState, index) => (
              <li
                key={slotState.pokemon.id}
                className={`team-builder__slot${draggedId === slotState.pokemon.id ? " team-builder__slot--dragging" : ""}`}
                draggable
                onDragStart={() => setDraggedId(slotState.pokemon.id)}
                onDragOver={(e) => {
                  e.preventDefault();
                  handleDragOverSlot(index);
                }}
                onDrop={(e) => e.preventDefault()}
                onDragEnd={() => setDraggedId(null)}
              >
                <span className="team-builder__slot-number">{index + 1}</span>

                <div className="team-builder__slot-main">
                  <span className="team-builder__drag-handle" aria-hidden="true">
                    ⠿
                  </span>
                  <img src={slotState.pokemon.sprite_url} alt={slotState.pokemon.name} />
                  <div className="team-builder__slot-info">
                    <Link
                      to={`/pokemon/${slotState.pokemon.name}`}
                      className="team-builder__slot-name"
                    >
                      {slotState.pokemon.name.replace(/-/g, " ")}
                    </Link>
                    <div className="team-builder__slot-types">
                      {slotState.pokemon.types.map((t) => (
                        <span
                          key={t}
                          className="team-builder__type-badge"
                          style={{ backgroundColor: typeColor(t) }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="team-builder__remove-btn"
                    onClick={() => handleRemove(index)}
                    aria-label="Remove from team"
                  >
                    ✕
                  </button>
                </div>

                <div className="team-builder__moves-grid">
                  {Array.from({ length: MAX_MOVES_PER_POKEMON }).map((_, moveSlotIndex) => {
                    const move = slotState.moves[moveSlotIndex];
                    const isSearching =
                      moveSearchTarget?.rosterIndex === index &&
                      moveSearchTarget?.moveSlotIndex === moveSlotIndex;

                    if (isSearching) {
                      return (
                        <div
                          key={moveSlotIndex}
                          className="team-builder__move-chip team-builder__move-chip--searching"
                        >
                          <MovePicker
                            pokemonId={slotState.pokemon.id}
                            excludeIds={slotState.moves.map((m) => m.id)}
                            onAdd={(move) => handleAddMove(index, move)}
                            onClose={() => setMoveSearchTarget(null)}
                          />
                        </div>
                      );
                    }

                    if (move) {
                      return (
                        <div
                          key={moveSlotIndex}
                          className="team-builder__move-chip team-builder__move-chip--filled"
                        >
                          <Link to={`/moves/${move.name}`} className="team-builder__move-link">
                            <DamageClassIcon damageClass={move.damage_class} size={13} />
                            <span>{move.name.replace(/-/g, " ")}</span>
                          </Link>
                          <button
                            type="button"
                            className="team-builder__move-remove"
                            onClick={() => handleRemoveMove(index, move.id)}
                            aria-label="Remove move"
                          >
                            ×
                          </button>
                        </div>
                      );
                    }

                    return (
                      <button
                        key={moveSlotIndex}
                        type="button"
                        className="team-builder__move-chip team-builder__move-chip--empty"
                        onClick={() => setMoveSearchTarget({ rosterIndex: index, moveSlotIndex })}
                      >
                        + Move
                      </button>
                    );
                  })}
                </div>
              </li>
            ))}
            {Array.from({ length: MAX_ROSTER_SIZE - roster.length }).map((_, i) =>
              searchSlotIndex === i ? (
                <li key={`empty-${i}`} className="team-builder__slot team-builder__slot--searching">
                  <span className="team-builder__slot-number">{roster.length + i + 1}</span>
                  <PokemonPicker
                    catalog={catalog}
                    excludeIds={currentIds}
                    onAdd={handleAdd}
                    onClose={() => setSearchSlotIndex(null)}
                  />
                </li>
              ) : (
                <li
                  key={`empty-${i}`}
                  className="team-builder__slot team-builder__slot--empty"
                  role="button"
                  tabIndex={0}
                  onClick={() => setSearchSlotIndex(i)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSearchSlotIndex(i);
                    }
                  }}
                >
                  <span className="team-builder__slot-number">{roster.length + i + 1}</span>
                  + Add Pokémon
                </li>
              ),
            )}
          </ol>
        </div>

        {error && <p className="team-builder__error">{error}</p>}

        <div className="team-builder__details-footer">
          <button
            type="button"
            className="team-builder__save-btn"
            disabled={saving || !isDirty || !name.trim()}
            onClick={handleSave}
          >
            {saving ? "Saving..." : "Save Team"}
          </button>
        </div>
      </div>
    </div>
  );
}
