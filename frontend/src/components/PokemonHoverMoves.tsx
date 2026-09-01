import { useNavigate } from "react-router-dom";
import { typeColor } from "./typeColors";
import "./PokemonHoverMoves.css";

export interface HoverMove {
  key: string | number;
  label: string;
  type: string | null;
  /** Path to the move's detail page, or null if it can't be linked (e.g. an
   * unresolved scraped move). Rendered as a click target inside the
   * tooltip, not a real <a> — the tooltip nests inside another clickable
   * element (a team row button, a Pokemon sprite link) in every current
   * usage, and nested interactive elements aren't valid HTML. */
  linkTo: string | null;
}

interface PokemonHoverMovesProps {
  spriteUrl: string | null;
  name: string;
  moves: HoverMove[];
  className?: string;
}

/** A Pokemon sprite that reveals its moveset in a small floating tooltip on
 * hover — shared by the homepage's Worlds cards and the team list's roster
 * preview, both of which show a row of sprites with no room for inline
 * move text. */
export function PokemonHoverMoves({ spriteUrl, name, moves, className }: PokemonHoverMovesProps) {
  const navigate = useNavigate();

  return (
    <span className={`pokemon-hover-moves${className ? ` ${className}` : ""}`}>
      {spriteUrl && <img src={spriteUrl} alt={name} loading="lazy" />}
      {moves.length > 0 && (
        <span className="pokemon-hover-moves__tooltip">
          <span className="pokemon-hover-moves__tooltip-box">
            <span className="pokemon-hover-moves__tooltip-name">{name.replace(/-/g, " ")}</span>
            <span className="pokemon-hover-moves__tooltip-list">
              {moves.map((m) => (
                <span
                  key={m.key}
                  className={`pokemon-hover-moves__tooltip-move${
                    m.linkTo ? " pokemon-hover-moves__tooltip-move--linked" : ""
                  }`}
                  onClick={(e) => {
                    if (!m.linkTo) return;
                    // Both matter: stopPropagation alone doesn't reliably
                    // stop an ancestor <Link> here — react-router's click
                    // handler checks event.defaultPrevented before it
                    // checks whether the event even reached it, so without
                    // preventDefault the ancestor still navigates to the
                    // Pokemon page a moment after this navigate() call.
                    e.preventDefault();
                    e.stopPropagation();
                    navigate(m.linkTo);
                  }}
                >
                  {m.type && (
                    <span
                      className="pokemon-hover-moves__tooltip-type-dot"
                      style={{ backgroundColor: typeColor(m.type) }}
                    />
                  )}
                  {m.label}
                </span>
              ))}
            </span>
          </span>
        </span>
      )}
    </span>
  );
}
