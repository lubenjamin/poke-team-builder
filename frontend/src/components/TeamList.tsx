import type { Team } from "../types/team";
import "./TeamList.css";

interface TeamListProps {
  teams: Team[];
  selectedId: number | null;
  isCreatingNew: boolean;
  onSelect: (id: number) => void;
  onNewTeam: () => void;
  onDelete: (id: number) => void;
}

export function TeamList({
  teams,
  selectedId,
  isCreatingNew,
  onSelect,
  onNewTeam,
  onDelete,
}: TeamListProps) {
  return (
    <div className="team-list">
      <button
        type="button"
        className={`team-list__new-btn${isCreatingNew ? " team-list__new-btn--active" : ""}`}
        onClick={onNewTeam}
      >
        + New Team
      </button>

      <ul className="team-list__items">
        {teams.map((team) => (
          <li
            key={team.id}
            className={`team-list__item${
              !isCreatingNew && team.id === selectedId ? " team-list__item--active" : ""
            }`}
          >
            <button type="button" className="team-list__name" onClick={() => onSelect(team.id)}>
              {team.name}
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
        {teams.length === 0 && !isCreatingNew && <li className="team-list__empty">No teams yet.</li>}
      </ul>
    </div>
  );
}
