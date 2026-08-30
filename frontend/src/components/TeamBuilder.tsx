import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { createTeam, fetchTeam, replaceRoster, updateTeam } from "../api/teams";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Team } from "../types/team";
import { RosterEditor, type RosterSlotDraft } from "./RosterEditor";
import "./TeamBuilder.css";

const MAX_ROSTER_SIZE = 6;
const NAME_MAX_LENGTH = 40;
const DESCRIPTION_MAX_LENGTH = 2500;

interface TeamBuilderProps {
  teamId: number | null; // null = new, unsaved team
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
  onSaved: (team: Team) => void;
  onDirtyChange: (dirty: boolean) => void;
}

function snapshotRoster(roster: RosterSlotDraft[]): string {
  return JSON.stringify(
    roster.map((r) => ({ pokemonId: r.pokemon.id, moveIds: r.moves.map((m) => m.id) })),
  );
}

export function TeamBuilder({
  teamId,
  catalog,
  moveCatalog,
  onSaved,
  onDirtyChange,
}: TeamBuilderProps) {
  const [status, setStatus] = useState<"loading" | "error" | "ready">(
    teamId === null ? "ready" : "loading",
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [roster, setRoster] = useState<RosterSlotDraft[]>([]);
  const [savedName, setSavedName] = useState("");
  const [savedDescription, setSavedDescription] = useState("");
  const [savedRosterSnapshot, setSavedRosterSnapshot] = useState("[]");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        const hydrated: RosterSlotDraft[] = data.roster.map((r) => ({
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

  const isDirty =
    name !== savedName ||
    description !== savedDescription ||
    snapshotRoster(roster) !== savedRosterSnapshot;

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

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
      const hydrated: RosterSlotDraft[] = updated.roster.map((r) => ({
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
          <RosterEditor
            roster={roster}
            onChange={setRoster}
            catalog={catalog}
            moveCatalog={moveCatalog}
            maxSize={MAX_ROSTER_SIZE}
          />
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
