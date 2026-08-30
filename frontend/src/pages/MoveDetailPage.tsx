import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchMove } from "../api/moves";
import { DamageClassIcon } from "../components/DamageClassIcon";
import { typeColor } from "../components/typeColors";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveDetail as MoveDetailType } from "../types/move";
import "./MoveDetailPage.css";

export function MoveDetailPage() {
  const { idOrName } = useParams<{ idOrName: string }>();
  const [move, setMove] = useState<MoveDetailType | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");

  useDocumentTitle(move ? move.name.replace(/-/g, " ") : "Move");

  useEffect(() => {
    if (!idOrName) return;
    let cancelled = false;
    setStatus("loading");
    fetchMove(idOrName)
      .then((data) => {
        if (cancelled) return;
        setMove(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [idOrName]);

  if (status === "loading") return <p className="move-detail__message">Loading move...</p>;
  if (status === "error" || !move) {
    return <p className="move-detail__message">Couldn't find that move.</p>;
  }

  return (
    <main className="move-detail">
      <div className="move-detail__header">
        <h1 className="move-detail__name">{move.name.replace(/-/g, " ")}</h1>
        <div className="move-detail__badges">
          <span className="move-detail__type-badge" style={{ backgroundColor: typeColor(move.type) }}>
            {move.type}
          </span>
          <span className="move-detail__damage-class">
            <DamageClassIcon damageClass={move.damage_class} />
            {move.damage_class}
          </span>
        </div>
      </div>

      {move.effect_text && <p className="move-detail__effect">{move.effect_text}</p>}

      <div className="move-detail__stats">
        <div className="move-detail__stat">
          <span className="move-detail__stat-label">Power</span>
          <span className="move-detail__stat-value">{move.power ?? "—"}</span>
        </div>
        <div className="move-detail__stat">
          <span className="move-detail__stat-label">Accuracy</span>
          <span className="move-detail__stat-value">
            {move.accuracy != null ? `${move.accuracy}%` : "—"}
          </span>
        </div>
        <div className="move-detail__stat">
          <span className="move-detail__stat-label">PP</span>
          <span className="move-detail__stat-value">{move.pp ?? "—"}</span>
        </div>
        <div className="move-detail__stat">
          <span className="move-detail__stat-label">Priority</span>
          <span className="move-detail__stat-value">{move.priority}</span>
        </div>
      </div>

      <h2 className="move-detail__section-title">Pokémon that can learn {move.name.replace(/-/g, " ")}</h2>
      <div className="move-detail__pokemon-grid">
        {move.learnable_by.map((pokemon) => (
          <Link key={pokemon.id} to={`/pokemon/${pokemon.name}`} className="move-detail__pokemon-card">
            <img src={pokemon.sprite_url} alt={pokemon.name} />
            <span>{pokemon.name.replace(/-/g, " ")}</span>
          </Link>
        ))}
        {move.learnable_by.length === 0 && (
          <p className="move-detail__message">No Pokémon in this catalog learn this move.</p>
        )}
      </div>
    </main>
  );
}
