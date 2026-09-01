import { useState } from "react";
import { generateCounterTeam } from "../api/counterTeam";
import { ApiError } from "../api/client";
import { PageHero } from "../components/PageHero";
import { RosterEditor, type RosterSlotDraft } from "../components/RosterEditor";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import "./TeamOptimizerPage.css";

interface TeamOptimizerPageProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

export function TeamOptimizerPage({ catalog, moveCatalog }: TeamOptimizerPageProps) {
  useDocumentTitle("Team Optimizer");

  const [opponentRoster, setOpponentRoster] = useState<RosterSlotDraft[]>([]);
  const [generatedRoster, setGeneratedRoster] = useState<RosterSlotDraft[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isOpponentTeamComplete =
    opponentRoster.length === 6 && opponentRoster.every((slot) => slot.moves.length === 4);

  async function handleGenerate() {
    if (!isOpponentTeamComplete) {
      setError("Fill all 6 opponent slots with 4 moves each before generating");
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const roster = await generateCounterTeam(
        opponentRoster.map((r) => ({
          pokemon_id: r.pokemon.id,
          move_ids: r.moves.map((m) => m.id),
        })),
      );
      setGeneratedRoster(roster.map((r) => ({ pokemon: r.pokemon, moves: r.moves })));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to generate a counter team");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main>
      <PageHero
        title="Team Optimizer"
        description="Build out the team you're facing, then generate a counter team of your own."
      />

      <div className="optimizer-page__layout">
        <div className="optimizer-page__column">
          <div className="optimizer-page__column-header">
            <h2>Opponent's Team</h2>
            <span className="optimizer-page__count">{opponentRoster.length}/6</span>
          </div>
          <RosterEditor
            roster={opponentRoster}
            onChange={setOpponentRoster}
            catalog={catalog}
            moveCatalog={moveCatalog}
          />

          {error && <p className="optimizer-page__error">{error}</p>}

          <button
            type="button"
            className="optimizer-page__generate-btn"
            disabled={generating || !isOpponentTeamComplete}
            onClick={handleGenerate}
          >
            {generating ? "Generating..." : "Generate Counter Team"}
          </button>
        </div>

        <div className="optimizer-page__column">
          <div className="optimizer-page__column-header">
            <h2>Your Counter Team</h2>
            {generatedRoster && (
              <span className="optimizer-page__count">{generatedRoster.length}/6</span>
            )}
          </div>
          {generatedRoster ? (
            <RosterEditor
              roster={generatedRoster}
              onChange={() => {}}
              catalog={catalog}
              moveCatalog={moveCatalog}
              readOnly
            />
          ) : (
            <p className="optimizer-page__placeholder">
              Fill in the opponent's team and generate to see a counter team here.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
