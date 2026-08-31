import type { TeamPokemonSlot } from "../types/team";

interface TeamRosterStripProps {
  roster: TeamPokemonSlot[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

/** Read-only party-icon selector for the team details page — deliberately
 * not RosterEditor (that's drag/edit-oriented with full cards); this is
 * just a row of clickable sprite tiles. */
export function TeamRosterStrip({ roster, selectedIndex, onSelect }: TeamRosterStripProps) {
  return (
    <div className="team-roster-strip">
      {roster.map((slot, index) => (
        <button
          key={slot.pokemon.id}
          type="button"
          className={`team-roster-strip__tile${
            index === selectedIndex ? " team-roster-strip__tile--active" : ""
          }`}
          onClick={() => onSelect(index)}
        >
          <img src={slot.pokemon.sprite_url} alt={slot.pokemon.name} />
          <span>{slot.pokemon.name.replace(/-/g, " ")}</span>
        </button>
      ))}
    </div>
  );
}
