import { Link } from "react-router-dom";
import type { TeamPokemonSlot } from "../types/team";
import { typeColor } from "./typeColors";

interface CounterTeamPanelProps {
  roster: TeamPokemonSlot[];
  onSave: () => void;
  onDismiss: () => void;
  saving: boolean;
}

/** Preview of a generated counter team, shown inline on TeamDetailPage after
 * "Generate Counter Team" — read-only (no picker/editing, this is a result
 * to inspect and either save or discard, not a roster being built). */
export function CounterTeamPanel({ roster, onSave, onDismiss, saving }: CounterTeamPanelProps) {
  return (
    <section className="counter-team-panel">
      <div className="counter-team-panel__header">
        <h2 className="team-detail__section-title counter-team-panel__title">Counter Team</h2>
        <div className="counter-team-panel__actions">
          <button
            type="button"
            className="counter-team-panel__save-btn"
            onClick={onSave}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save as New Team"}
          </button>
          <button type="button" className="counter-team-panel__dismiss-btn" onClick={onDismiss}>
            Dismiss
          </button>
        </div>
      </div>

      <div className="counter-team-panel__grid">
        {roster.map((slot) => (
          <div key={slot.slot} className="counter-team-panel__card">
            <img src={slot.pokemon.sprite_url} alt={slot.pokemon.name} />
            <Link to={`/pokemon/${slot.pokemon.name}`} className="counter-team-panel__name">
              {slot.pokemon.name.replace(/-/g, " ")}
            </Link>
            <div className="counter-team-panel__types">
              {slot.pokemon.types.map((t) => (
                <span
                  key={t}
                  className="counter-team-panel__type-badge"
                  style={{ backgroundColor: typeColor(t) }}
                >
                  {t}
                </span>
              ))}
            </div>
            <div className="counter-team-panel__moves">
              {slot.moves.length > 0 ? (
                slot.moves.map((m) => (
                  <Link key={m.id} to={`/moves/${m.name}`} className="counter-team-panel__move">
                    {m.name.replace(/-/g, " ")}
                  </Link>
                ))
              ) : (
                <span className="counter-team-panel__move counter-team-panel__move--empty">
                  No moves
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
