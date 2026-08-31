import { Link } from "react-router-dom";
import type { TeamPokemonSlot } from "../types/team";
import type { Pokemon } from "../types/pokemon";
import { DamageClassIcon } from "./DamageClassIcon";
import { typeColor } from "./typeColors";

const STAT_MAX = 255; // historical max for any single base stat (e.g. Blissey's HP)

const STATS: { key: keyof Pokemon; label: string }[] = [
  { key: "hp", label: "HP" },
  { key: "attack", label: "Attack" },
  { key: "defense", label: "Defense" },
  { key: "special_attack", label: "Sp. Attack" },
  { key: "special_defense", label: "Sp. Defense" },
  { key: "speed", label: "Speed" },
];

interface SlotDetailCardProps {
  slot: TeamPokemonSlot;
}

/** The currently-selected roster slot's full detail: name/types, its 4
 * equipped moves, and base stats — same fields PokemonDetailPage shows for
 * a single Pokemon, applied here to one team slot. No item/ability/nature
 * (not in this app's data model — v2/not built, see CLAUDE.md). */
export function SlotDetailCard({ slot }: SlotDetailCardProps) {
  const { pokemon, moves } = slot;

  return (
    <section className="slot-detail-card">
      <div className="slot-detail-card__header">
        <img src={pokemon.sprite_url} alt={pokemon.name} />
        <div>
          <div className="slot-detail-card__name-row">
            <Link to={`/pokemon/${pokemon.name}`} className="slot-detail-card__name">
              {pokemon.name.replace(/-/g, " ")}
            </Link>
            <span className="slot-detail-card__slot-badge">SLOT {slot.slot + 1}</span>
          </div>
          <div className="slot-detail-card__types">
            {pokemon.types.map((t) => (
              <span
                key={t}
                className="slot-detail-card__type-badge"
                style={{ backgroundColor: typeColor(t) }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      <h3 className="slot-detail-card__section-title">Moves</h3>
      <div className="slot-detail-card__moves">
        {Array.from({ length: 4 }).map((_, i) => {
          const move = moves[i];
          if (!move) {
            return (
              <div key={i} className="slot-detail-card__move slot-detail-card__move--empty" />
            );
          }
          return (
            <Link key={move.id} to={`/moves/${move.name}`} className="slot-detail-card__move">
              <span className="slot-detail-card__move-name">{move.name.replace(/-/g, " ")}</span>
              <span className="slot-detail-card__move-footer">
                <span
                  className="slot-detail-card__move-type"
                  style={{ backgroundColor: typeColor(move.type) }}
                >
                  {move.type}
                </span>
                <DamageClassIcon damageClass={move.damage_class} size={14} />
              </span>
            </Link>
          );
        })}
      </div>

      <h3 className="slot-detail-card__section-title">Stats</h3>
      <div className="stat-bars">
        {STATS.map(({ key, label }) => {
          const value = pokemon[key] as number;
          return (
            <div className="stat-bar" key={key}>
              <span className="stat-bar__label">{label}</span>
              <div className="stat-bar__track">
                <div
                  className="stat-bar__fill"
                  style={{ width: `${Math.min(100, (value / STAT_MAX) * 100)}%` }}
                />
              </div>
              <span className="stat-bar__value">{value}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
