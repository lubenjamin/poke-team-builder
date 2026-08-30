import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchPokemonDetail } from "../api/pokemon";
import { DamageClassIcon } from "../components/DamageClassIcon";
import { typeColor } from "../components/typeColors";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { PokemonDetail as PokemonDetailType } from "../types/pokemon";
import "./PokemonDetailPage.css";

const STAT_MAX = 255; // historical max for any single base stat (e.g. Blissey's HP)

const STATS: { key: keyof PokemonDetailType; label: string }[] = [
  { key: "hp", label: "HP" },
  { key: "attack", label: "Attack" },
  { key: "defense", label: "Defense" },
  { key: "special_attack", label: "Sp. Attack" },
  { key: "special_defense", label: "Sp. Defense" },
  { key: "speed", label: "Speed" },
];

export function PokemonDetailPage() {
  const { idOrName } = useParams<{ idOrName: string }>();
  const [pokemon, setPokemon] = useState<PokemonDetailType | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");

  useDocumentTitle(pokemon ? pokemon.name.replace(/-/g, " ") : "Pokémon");

  useEffect(() => {
    if (!idOrName) return;
    let cancelled = false;
    setStatus("loading");
    fetchPokemonDetail(idOrName)
      .then((data) => {
        if (cancelled) return;
        setPokemon(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [idOrName]);

  if (status === "loading") return <p className="pokemon-detail__message">Loading Pokémon...</p>;
  if (status === "error" || !pokemon) {
    return <p className="pokemon-detail__message">Couldn't find that Pokémon.</p>;
  }

  const weak = Object.entries(pokemon.type_effectiveness)
    .filter(([, m]) => m > 1)
    .sort((a, b) => b[1] - a[1]);
  const resist = Object.entries(pokemon.type_effectiveness)
    .filter(([, m]) => m < 1 && m > 0)
    .sort((a, b) => a[1] - b[1]);
  const immune = Object.entries(pokemon.type_effectiveness).filter(([, m]) => m === 0);

  const learnableMoves = [...pokemon.learnable_moves].sort(
    (a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name),
  );

  return (
    <main className="pokemon-detail">
      <div className="pokemon-detail__header">
        <img className="pokemon-detail__sprite" src={pokemon.sprite_url} alt={pokemon.name} />
        <div>
          <span className="pokemon-detail__dex-number">
            #{pokemon.pokedex_number.toString().padStart(4, "0")}
          </span>
          <h1 className="pokemon-detail__name">{pokemon.name.replace(/-/g, " ")}</h1>
          <div className="pokemon-detail__types">
            {pokemon.types.map((t) => (
              <span key={t} className="pokemon-detail__type-badge" style={{ backgroundColor: typeColor(t) }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      <h2 className="pokemon-detail__section-title">Base stats</h2>
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

      <h2 className="pokemon-detail__section-title">Type effectiveness</h2>
      <div className="type-effectiveness">
        <TypeEffectivenessGroup label="Weak to" entries={weak} />
        <TypeEffectivenessGroup label="Resists" entries={resist} />
        <TypeEffectivenessGroup label="Immune to" entries={immune} />
      </div>

      <h2 className="pokemon-detail__section-title">
        Learnable moves ({learnableMoves.length})
      </h2>
      <ul className="pokemon-detail__moves">
        {learnableMoves.map((move) => (
          <li key={move.id}>
            <Link to={`/moves/${move.name}`} className="pokemon-detail__move-link">
              <span>{move.name.replace(/-/g, " ")}</span>
              <span
                className="pokemon-detail__move-type"
                style={{ backgroundColor: typeColor(move.type) }}
              >
                {move.type}
              </span>
              <DamageClassIcon damageClass={move.damage_class} size={16} />
            </Link>
          </li>
        ))}
        {learnableMoves.length === 0 && (
          <p className="pokemon-detail__message">No moves recorded for this Pokémon.</p>
        )}
      </ul>
    </main>
  );
}

interface TypeEffectivenessGroupProps {
  label: string;
  entries: [string, number][];
}

function TypeEffectivenessGroup({ label, entries }: TypeEffectivenessGroupProps) {
  if (entries.length === 0) return null;
  return (
    <div className="type-effectiveness__group">
      <span className="type-effectiveness__group-label">{label}</span>
      <div className="type-effectiveness__badges">
        {entries.map(([type, multiplier]) => (
          <span key={type} className="type-effectiveness__badge" style={{ backgroundColor: typeColor(type) }}>
            {type} ×{multiplier}
          </span>
        ))}
      </div>
    </div>
  );
}
