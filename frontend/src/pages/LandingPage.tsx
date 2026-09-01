import { Link } from "react-router-dom";
import worldsData from "../data/vgcWorlds2026.json";
import { PokemonHoverMoves } from "../components/PokemonHoverMoves";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { VgcWorldsEntry } from "../types/vgcWorlds";
import "./LandingPage.css";

const worlds = worldsData as VgcWorldsEntry[];

export function LandingPage() {
  useDocumentTitle("Pokétactics");

  return (
    <main className="landing">
      <section className="landing__hero">
        <div className="landing__hero-actions">
          <Link to="/pokedex" className="landing__cta landing__cta--primary">
            Browse Pokédex
          </Link>
          <Link to="/teams" className="landing__cta">
            My Teams
          </Link>
        </div>
      </section>

      <section className="landing__worlds">
        <div className="landing__worlds-header">
          <h2>World Championships 2026 — Top 8</h2>
          <p className="landing__worlds-subtitle">
            Real rosters from the top 8 finishers, sourced from{" "}
            <a href="https://limitlessvgc.com/tournaments/437" target="_blank" rel="noreferrer">
              limitlessvgc.com
            </a>
            .
          </p>
        </div>

        <div className="landing__worlds-grid">
          {worlds.map((entry) => (
            <article key={entry.rank} className="worlds-card">
              <div className="worlds-card__header">
                <span className="worlds-card__placement">{entry.placement}</span>
                <span className="worlds-card__player">
                  {entry.player_name}
                  <span className="worlds-card__country">{entry.country}</span>
                </span>
              </div>

              <div className="worlds-card__roster">
                {entry.pokemon.map((p) => (
                  <Link
                    key={p.slug}
                    to={p.resolved_id ? `/pokemon/${p.slug}` : "#"}
                    className="worlds-mon-link"
                    onClick={(e) => {
                      if (!p.resolved_id) e.preventDefault();
                    }}
                  >
                    <PokemonHoverMoves
                      spriteUrl={p.sprite_url}
                      name={p.display_name}
                      moves={p.moves.map((m) => ({
                        key: m.display_name,
                        label: m.display_name,
                        type: m.type,
                        linkTo: m.resolved_id ? `/moves/${m.resolved_id}` : null,
                      }))}
                      className="worlds-mon-sprite"
                    />
                  </Link>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
