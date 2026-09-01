import { PokemonHoverMoves } from "./PokemonHoverMoves";
import type { TeamDetail } from "../types/team";
import "./TeamList.css";

interface TeamListProps {
  teams: TeamDetail[];
  onSelect: (id: number) => void;
  onNewTeam: () => void;
  onDelete: (id: number) => void;
}

export function TeamList({ teams, onSelect, onNewTeam, onDelete }: TeamListProps) {
  return (
    <div className="team-list">
      <button type="button" className="team-list__new-btn" onClick={onNewTeam}>
        + New Team
      </button>

      <ul className="team-list__items">
        {teams.map((team) => (
          <li key={team.id} className="team-list__item">
            <button
              type="button"
              className="team-list__row"
              onClick={() => onSelect(team.id)}
            >
              <span className="team-list__name">{team.name}</span>
              <div className="team-list__roster-preview">
                {team.roster.map((slot) => (
                  <PokemonHoverMoves
                    key={slot.pokemon.id}
                    spriteUrl={slot.pokemon.sprite_url}
                    name={slot.pokemon.name}
                    moves={slot.moves.map((m) => ({
                      key: m.id,
                      label: m.name.replace(/-/g, " "),
                      type: m.type,
                      linkTo: `/moves/${m.name}`,
                    }))}
                    className="team-list__roster-preview-mon"
                  />
                ))}
                {team.roster.length === 0 && (
                  <span className="team-list__roster-preview-empty">Empty</span>
                )}
              </div>
            </button>
            <button
              type="button"
              className="team-list__icon-btn"
              aria-label={`Delete ${team.name}`}
              onClick={() => {
                if (confirm(`Delete "${team.name}"? This can't be undone.`)) onDelete(team.id);
              }}
            >
              ✕
            </button>
          </li>
        ))}
        {teams.length === 0 && <li className="team-list__empty">No teams yet.</li>}
      </ul>
    </div>
  );
}
