import { useState } from "react";
import type { TeamPokemonSlot } from "../types/team";

type SpeedTab = "base" | "tailwind" | "trick-room";

const TABS: { key: SpeedTab; label: string }[] = [
  { key: "base", label: "Base" },
  { key: "tailwind", label: "Tailwind" },
  { key: "trick-room", label: "Trick Room" },
];

interface TeamSpeedTiersProps {
  roster: TeamPokemonSlot[];
}

/** Speed order under three conditions: Base (raw speed stat, fastest
 * first), Tailwind (speed doubled, fastest first), Trick Room (raw speed,
 * but SLOWEST goes first — turn order inverts, the stat itself doesn't
 * change). Each member keeps a fixed color tied to its roster slot (not
 * its rank) across tab switches, so its bar stays identifiable as the
 * order reshuffles. */
export function TeamSpeedTiers({ roster }: TeamSpeedTiersProps) {
  const [tab, setTab] = useState<SpeedTab>("base");

  const rows = roster.map((slot, index) => ({
    slot,
    seriesIndex: index,
    value: tab === "tailwind" ? slot.pokemon.speed * 2 : slot.pokemon.speed,
  }));

  const sorted =
    tab === "trick-room"
      ? [...rows].sort((a, b) => a.value - b.value)
      : [...rows].sort((a, b) => b.value - a.value);

  const max = Math.max(...rows.map((r) => r.value), 1);
  const min = Math.min(...rows.map((r) => r.value), 0);

  return (
    <div className="team-speed-tiers">
      <div className="team-speed-tiers__tabs">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            className={`team-speed-tiers__tab${tab === key ? " team-speed-tiers__tab--active" : ""}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "trick-room" && (
        <p className="team-speed-tiers__hint">Slowest goes first in Trick Room.</p>
      )}
      <ol className="team-speed-tiers__list">
        {sorted.map(({ slot, seriesIndex, value }, rank) => (
          <li key={slot.pokemon.id} className="team-speed-tiers__row">
            <span className="team-speed-tiers__rank">#{rank + 1}</span>
            <span className="team-speed-tiers__name">{slot.pokemon.name.replace(/-/g, " ")}</span>
            <div className="team-speed-tiers__track">
              <div
                className="team-speed-tiers__fill"
                style={{
                  width: `${Math.max(4, (value / max) * 100)}%`,
                  backgroundColor: `var(--team-series-${(seriesIndex % 6) + 1})`,
                }}
              />
            </div>
            <span className="team-speed-tiers__value">{value}</span>
          </li>
        ))}
      </ol>
      <div className="team-speed-tiers__range">
        <span>
          Fastest {sorted[0]?.slot.pokemon.name.replace(/-/g, " ")} · {sorted[0]?.value}
        </span>
        <span>
          Range {min} → {max}
        </span>
      </div>
    </div>
  );
}
