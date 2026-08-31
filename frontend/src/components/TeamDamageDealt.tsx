import type { TeamPokemonSlot } from "../types/team";
import { TYPE_COLORS, typeColor } from "./typeColors";

const ALL_TYPES = Object.keys(TYPE_COLORS);

interface TeamDamageDealtProps {
  roster: TeamPokemonSlot[];
  matrix: Record<string, Record<string, number>>;
}

interface DealtEntry {
  type: string;
  count: number;
  maxMultiplier: number;
}

function computeDealt(
  roster: TeamPokemonSlot[],
  matrix: Record<string, Record<string, number>>,
): DealtEntry[] {
  return ALL_TYPES.map((defendingType) => {
    let count = 0;
    let maxMultiplier = 0;
    for (const slot of roster) {
      const memberBest = slot.moves.reduce(
        (best, move) => Math.max(best, matrix[move.type]?.[defendingType] ?? 1),
        0,
      );
      if (memberBest > 1) {
        count += 1;
        maxMultiplier = Math.max(maxMultiplier, memberBest);
      }
    }
    return { type: defendingType, count, maxMultiplier };
  });
}

/** For each of the 18 types (as a defender), how many team members have at
 * least one equipped move that's super-effective against it — a pip meter
 * (filled = threatening members, out of the team size) plus the strongest
 * multiplier any of them achieves. */
export function TeamDamageDealt({ roster, matrix }: TeamDamageDealtProps) {
  const entries = computeDealt(roster, matrix);
  const teamSize = roster.length;

  return (
    <div className="team-damage-dealt">
      {entries.map(({ type, count, maxMultiplier }) => (
        <div key={type} className="team-damage-dealt__card">
          <span
            className="team-damage-dealt__type-badge"
            style={{ backgroundColor: typeColor(type) }}
          >
            {type}
          </span>
          <div className="team-damage-dealt__pips">
            {Array.from({ length: teamSize }).map((_, i) => (
              <span
                key={i}
                className={`team-damage-dealt__pip${i < count ? " team-damage-dealt__pip--filled" : ""}`}
              />
            ))}
          </div>
          <span className="team-damage-dealt__label">
            {count > 0 ? `${maxMultiplier}× SE` : "Neutral"}
          </span>
        </div>
      ))}
    </div>
  );
}
