import { Link } from "react-router-dom";
import type { Move } from "../types/move";
import { DamageClassIcon } from "./DamageClassIcon";
import { typeColor } from "./typeColors";
import "./MoveCard.css";

interface MoveCardProps {
  move: Move;
}

export function MoveCard({ move }: MoveCardProps) {
  return (
    <Link
      to={`/moves/${move.name}`}
      className="move-card"
      style={{ backgroundColor: `${typeColor(move.type)}26` }}
    >
      <h3 className="move-card__name">{move.name.replace(/-/g, " ")}</h3>
      {move.effect_text && <p className="move-card__description">{move.effect_text}</p>}
      <div className="move-card__footer">
        <span className="move-card__type-badge" style={{ backgroundColor: typeColor(move.type) }}>
          {move.type}
        </span>
        <DamageClassIcon damageClass={move.damage_class} size={16} />
        <span className="move-card__stats">
          {move.power != null && <span>{move.power} BP</span>}
          {move.accuracy != null && <span>{move.accuracy}%</span>}
          {move.pp != null && <span>{move.pp} PP</span>}
        </span>
      </div>
    </Link>
  );
}
