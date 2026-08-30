import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Move } from "../types/move";
import type { Pokemon } from "../types/pokemon";
import { DamageClassIcon } from "./DamageClassIcon";
import { MovePicker } from "./MovePicker";
import { PokemonPicker } from "./PokemonPicker";
import "./RosterEditor.css";
import { typeColor } from "./typeColors";

const MAX_MOVES_PER_POKEMON = 4;

export interface RosterSlotDraft {
  pokemon: Pokemon;
  moves: Move[];
}

interface MoveSearchTarget {
  rosterIndex: number;
  moveSlotIndex: number;
}

interface RosterEditorProps {
  roster: RosterSlotDraft[];
  onChange: (roster: RosterSlotDraft[]) => void;
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
  maxSize?: number;
  /** Display-only: no drag, no add/remove Pokemon or moves. Used for showing
   * a generated team you can't edit, in the same visual/interactive shell as
   * the editable roster (clicking a Pokemon/move still navigates). */
  readOnly?: boolean;
}

/** The shared roster-of-up-to-6-Pokemon-with-moves editor — used by
 * TeamBuilder (wrapped with name/description/save) and TeamOptimizerPage
 * (the opponent-input side, and read-only for the generated side). Pulled
 * out of TeamBuilder once a second place needed the exact same interactive
 * UI, rather than rebuilding a lookalike. */
export function RosterEditor({
  roster,
  onChange,
  catalog,
  moveCatalog,
  maxSize = 6,
  readOnly = false,
}: RosterEditorProps) {
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [searchSlotIndex, setSearchSlotIndex] = useState<number | null>(null);
  const [moveSearchTarget, setMoveSearchTarget] = useState<MoveSearchTarget | null>(null);

  // Built once per catalog load (not per picker open) so resolving a
  // Pokemon's learnable moves is a synchronous Map lookup with no network
  // round trip or repeated O(n) scan, no matter how many move slots get
  // opened in this session.
  const moveById = useMemo(
    () => new Map(moveCatalog.moves.map((m) => [m.id, m] as const)),
    [moveCatalog.moves],
  );

  const currentDexNumbers = roster.map((r) => r.pokemon.pokedex_number);

  function handleAdd(pokemon: Pokemon) {
    if (roster.length >= maxSize || currentDexNumbers.includes(pokemon.pokedex_number)) return;
    onChange([...roster, { pokemon, moves: [] }]);
    setSearchSlotIndex(null);
  }

  function handleRemove(index: number) {
    onChange(roster.filter((_, i) => i !== index));
  }

  function handleDragOverSlot(targetIndex: number) {
    if (draggedId === null) return;
    const currentIndex = roster.findIndex((r) => r.pokemon.id === draggedId);
    if (currentIndex === -1 || currentIndex === targetIndex) return;
    const next = [...roster];
    const [moved] = next.splice(currentIndex, 1);
    next.splice(targetIndex, 0, moved);
    onChange(next);
  }

  function handleAddMove(rosterIndex: number, move: Move) {
    const slot = roster[rosterIndex];
    if (slot.moves.length >= MAX_MOVES_PER_POKEMON || slot.moves.some((m) => m.id === move.id)) {
      return;
    }
    const next = [...roster];
    const updatedMoves = [...slot.moves, move];
    next[rosterIndex] = { ...slot, moves: updatedMoves };
    onChange(next);
    // Moves fill left-to-right, so the next empty slot (if any) is always
    // right after the one just filled — jump straight into it instead of
    // making the user click "+ Move" again for each of the 4 slots.
    setMoveSearchTarget(
      updatedMoves.length < MAX_MOVES_PER_POKEMON
        ? { rosterIndex, moveSlotIndex: updatedMoves.length }
        : null,
    );
  }

  function handleRemoveMove(rosterIndex: number, moveId: number) {
    const slot = roster[rosterIndex];
    const next = [...roster];
    next[rosterIndex] = { ...slot, moves: slot.moves.filter((m) => m.id !== moveId) };
    onChange(next);
  }

  return (
    <ol className="roster-editor">
      {roster.map((slotState, index) => (
        <li
          key={slotState.pokemon.id}
          className={`roster-editor__slot${draggedId === slotState.pokemon.id ? " roster-editor__slot--dragging" : ""}${moveSearchTarget?.rosterIndex === index ? " roster-editor__slot--move-searching" : ""}`}
          draggable={!readOnly}
          onDragStart={() => {
            if (!readOnly) setDraggedId(slotState.pokemon.id);
          }}
          onDragOver={(e) => {
            if (readOnly) return;
            e.preventDefault();
            handleDragOverSlot(index);
          }}
          onDrop={(e) => e.preventDefault()}
          onDragEnd={() => setDraggedId(null)}
        >
          <span className="roster-editor__slot-number">{index + 1}</span>

          <div className="roster-editor__slot-main">
            {!readOnly && (
              <span className="roster-editor__drag-handle" aria-hidden="true">
                ⠿
              </span>
            )}
            <img src={slotState.pokemon.sprite_url} alt={slotState.pokemon.name} />
            <div className="roster-editor__slot-info">
              <Link to={`/pokemon/${slotState.pokemon.name}`} className="roster-editor__slot-name">
                {slotState.pokemon.name.replace(/-/g, " ")}
              </Link>
              <div className="roster-editor__slot-types">
                {slotState.pokemon.types.map((t) => (
                  <span
                    key={t}
                    className="roster-editor__type-badge"
                    style={{ backgroundColor: typeColor(t) }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
            {!readOnly && (
              <button
                type="button"
                className="roster-editor__remove-btn"
                onClick={() => handleRemove(index)}
                aria-label="Remove from team"
              >
                ✕
              </button>
            )}
          </div>

          <div className="roster-editor__moves-grid">
            {Array.from({ length: MAX_MOVES_PER_POKEMON }).map((_, moveSlotIndex) => {
              const move = slotState.moves[moveSlotIndex];
              const isSearching =
                !readOnly &&
                moveSearchTarget?.rosterIndex === index &&
                moveSearchTarget?.moveSlotIndex === moveSlotIndex;

              if (isSearching) {
                return (
                  <div
                    key={moveSlotIndex}
                    className="roster-editor__move-chip roster-editor__move-chip--searching"
                  >
                    <MovePicker
                      pokemon={slotState.pokemon}
                      moveById={moveById}
                      moveCatalogStatus={moveCatalog.status}
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
                    className="roster-editor__move-chip roster-editor__move-chip--filled"
                  >
                    <Link to={`/moves/${move.name}`} className="roster-editor__move-name">
                      {move.name.replace(/-/g, " ")}
                    </Link>
                    <div className="roster-editor__move-footer">
                      <span
                        className="roster-editor__move-type-badge"
                        style={{ backgroundColor: typeColor(move.type) }}
                      >
                        {move.type}
                      </span>
                      <DamageClassIcon damageClass={move.damage_class} size={14} />
                    </div>
                    {!readOnly && (
                      <button
                        type="button"
                        className="roster-editor__move-remove"
                        onClick={() => handleRemoveMove(index, move.id)}
                        aria-label="Remove move"
                      >
                        ×
                      </button>
                    )}
                  </div>
                );
              }

              if (readOnly) {
                return (
                  <div
                    key={moveSlotIndex}
                    className="roster-editor__move-chip roster-editor__move-chip--empty-readonly"
                  />
                );
              }

              return (
                <button
                  key={moveSlotIndex}
                  type="button"
                  className="roster-editor__move-chip roster-editor__move-chip--empty"
                  onClick={() => setMoveSearchTarget({ rosterIndex: index, moveSlotIndex })}
                >
                  + Move
                </button>
              );
            })}
          </div>
        </li>
      ))}
      {!readOnly &&
        Array.from({ length: maxSize - roster.length }).map((_, i) =>
          searchSlotIndex === i ? (
            <li key={`empty-${i}`} className="roster-editor__slot roster-editor__slot--searching">
              <span className="roster-editor__slot-number">{roster.length + i + 1}</span>
              <PokemonPicker
                catalog={catalog}
                excludeDexNumbers={currentDexNumbers}
                onAdd={handleAdd}
                onClose={() => setSearchSlotIndex(null)}
              />
            </li>
          ) : (
            <li
              key={`empty-${i}`}
              className="roster-editor__slot roster-editor__slot--empty"
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
              <span className="roster-editor__slot-number">{roster.length + i + 1}</span>
              + Add Pokémon
            </li>
          ),
        )}
    </ol>
  );
}
