import type { TeamPokemonSlot } from "../types/team";
import { TYPE_COLORS, typeColor } from "./typeColors";

const ALL_TYPES = Object.keys(TYPE_COLORS);

interface TeamDefenseMatrixProps {
  roster: TeamPokemonSlot[];
  matrix: Record<string, Record<string, number>>;
}

function combinedMultiplier(
  matrix: Record<string, Record<string, number>>,
  attackingType: string,
  defendingTypes: string[],
): number {
  return defendingTypes.reduce((acc, t) => acc * (matrix[attackingType]?.[t] ?? 1), 1);
}

// 0x (immune) is left uncolored, same as 1x (neutral) — only genuinely
// non-zero weak (>1) and non-zero resist (0 < x < 1) values get a
// weak(red)/resist(blue) highlight; the printed "0×" already says immune
// plainly without needing its own color.
function cellClass(multiplier: number): string {
  if (multiplier === 0.25) return "team-defense-matrix__cell--resist-strong";
  if (multiplier > 0 && multiplier < 1) return "team-defense-matrix__cell--resist-mild";
  if (multiplier === 2) return "team-defense-matrix__cell--weak-mild";
  if (multiplier > 2) return "team-defense-matrix__cell--weak-strong";
  return "";
}

function netClass(net: number): string {
  if (net < 0) return "team-defense-matrix__summary--negative";
  if (net > 0) return "team-defense-matrix__summary--positive";
  return "";
}

function formatMultiplier(multiplier: number): string {
  return multiplier === 1 ? "1×" : `${multiplier}×`;
}

/** For each of the 18 attacking types, how each team member's (1-2)
 * defending types combine against it (multiplying, same as the backend's
 * compute_type_effectiveness — just run here per member against the full
 * fetched matrix instead of server-side for one Pokemon), plus per-row
 * WEAK/RESIST/NET summary counts across the team. */
export function TeamDefenseMatrix({ roster, matrix }: TeamDefenseMatrixProps) {
  return (
    <div className="team-defense-matrix">
      <div className="team-defense-matrix__scroll">
        <table>
          <thead>
            <tr>
              <th className="team-defense-matrix__type-col">Type</th>
              {roster.map((slot) => (
                <th key={slot.pokemon.id} className="team-defense-matrix__member-col">
                  <img src={slot.pokemon.sprite_url} alt={slot.pokemon.name} />
                </th>
              ))}
              <th>Resist</th>
              <th>Weak</th>
              <th>Net</th>
            </tr>
          </thead>
          <tbody>
            {ALL_TYPES.map((attackingType) => {
              const values = roster.map((slot) =>
                combinedMultiplier(
                  matrix,
                  attackingType,
                  slot.pokemon.types,
                ),
              );
              const weak = values.filter((v) => v > 1).length;
              const resist = values.filter((v) => v < 1).length;
              return (
                <tr key={attackingType}>
                  <td className="team-defense-matrix__type-col">
                    <span
                      className="team-defense-matrix__type-badge"
                      style={{ backgroundColor: typeColor(attackingType) }}
                    >
                      {attackingType}
                    </span>
                  </td>
                  {values.map((v, i) => (
                    <td key={roster[i].pokemon.id} className={cellClass(v)}>
                      {formatMultiplier(v)}
                    </td>
                  ))}
                  <td className="team-defense-matrix__summary">{resist}</td>
                  <td className="team-defense-matrix__summary">{weak}</td>
                  <td className={`team-defense-matrix__summary ${netClass(resist - weak)}`}>
                    {resist - weak}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
