import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { generateCounterTeamForTeam, saveCounterTeamForTeam } from "../api/counterTeam";
import { fetchTeam } from "../api/teams";
import { ApiError } from "../api/client";
import { CounterTeamPanel } from "../components/CounterTeamPanel";
import { SlotDetailCard } from "../components/SlotDetailCard";
import { TeamDamageDealt } from "../components/TeamDamageDealt";
import { TeamDefenseMatrix } from "../components/TeamDefenseMatrix";
import { TeamRosterStrip } from "../components/TeamRosterStrip";
import { TeamSpeedTiers } from "../components/TeamSpeedTiers";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useTypeEffectiveness } from "../hooks/useTypeEffectiveness";
import type { TeamDetail, TeamPokemonSlot } from "../types/team";
import "./TeamDetailPage.css";

export function TeamDetailPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const typeEffectiveness = useTypeEffectiveness();

  const [counterTeam, setCounterTeam] = useState<TeamPokemonSlot[] | null>(null);
  const [generatingCounter, setGeneratingCounter] = useState(false);
  const [savingCounter, setSavingCounter] = useState(false);
  const [counterError, setCounterError] = useState<string | null>(null);

  useDocumentTitle(team ? team.name : "Team");

  useEffect(() => {
    if (!teamId) return;
    let cancelled = false;
    setStatus("loading");
    fetchTeam(Number(teamId))
      .then((data) => {
        if (cancelled) return;
        setTeam(data);
        setSelectedIndex(0);
        setCounterTeam(null);
        setCounterError(null);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [teamId]);

  async function handleGenerateCounter() {
    if (!team) return;
    setGeneratingCounter(true);
    setCounterError(null);
    try {
      const roster = await generateCounterTeamForTeam(team.id);
      setCounterTeam(roster);
    } catch (err) {
      setCounterError(err instanceof ApiError ? err.message : "Failed to generate a counter team");
    } finally {
      setGeneratingCounter(false);
    }
  }

  async function handleSaveCounter() {
    if (!team) return;
    setSavingCounter(true);
    setCounterError(null);
    try {
      const newTeam = await saveCounterTeamForTeam(team.id);
      navigate(`/teams/${newTeam.id}`);
    } catch (err) {
      setCounterError(err instanceof ApiError ? err.message : "Failed to save the counter team");
      setSavingCounter(false);
    }
  }

  if (status === "loading") return <p className="team-detail__message">Loading team...</p>;
  if (status === "error" || !team) {
    return <p className="team-detail__message">Couldn't find that team.</p>;
  }

  if (team.roster.length === 0) {
    return (
      <main className="team-detail">
        <div className="team-detail__header">
          <div>
            <h1 className="team-detail__name">{team.name}</h1>
          </div>
          <Link to={`/teams/${team.id}/edit`} className="team-detail__edit-btn">
            Edit Team
          </Link>
        </div>
        <p className="team-detail__message">
          This team has no Pokémon yet — edit it to build out a roster.
        </p>
      </main>
    );
  }

  const selectedSlot = team.roster[selectedIndex] ?? team.roster[0];

  return (
    <main className="team-detail">
      <div className="team-detail__header">
        <div>
          <h1 className="team-detail__name">{team.name}</h1>
          {team.description && <p className="team-detail__description">{team.description}</p>}
        </div>
        <div className="team-detail__header-actions">
          <button
            type="button"
            className="team-detail__counter-btn"
            onClick={handleGenerateCounter}
            disabled={generatingCounter}
          >
            {generatingCounter ? "Generating..." : "Generate Counter Team"}
          </button>
          <button
            type="button"
            className="team-detail__edit-btn"
            onClick={() => navigate(`/teams/${team.id}/edit`)}
          >
            Edit Team
          </button>
        </div>
      </div>

      {counterError && <p className="team-detail__counter-error">{counterError}</p>}

      {counterTeam && (
        <CounterTeamPanel
          roster={counterTeam}
          onSave={handleSaveCounter}
          onDismiss={() => setCounterTeam(null)}
          saving={savingCounter}
        />
      )}

      <TeamRosterStrip
        roster={team.roster}
        selectedIndex={selectedIndex}
        onSelect={setSelectedIndex}
      />
      <SlotDetailCard slot={selectedSlot} />

      <h2 className="team-detail__section-title">Defense matrix</h2>
      {typeEffectiveness.status === "ready" ? (
        <TeamDefenseMatrix roster={team.roster} matrix={typeEffectiveness.data} />
      ) : (
        <p className="team-detail__message">
          {typeEffectiveness.status === "error" ? "Couldn't load type data." : "Loading..."}
        </p>
      )}

      <h2 className="team-detail__section-title">Damage dealt</h2>
      {typeEffectiveness.status === "ready" && (
        <TeamDamageDealt roster={team.roster} matrix={typeEffectiveness.data} />
      )}

      <h2 className="team-detail__section-title">Speed tiers</h2>
      <TeamSpeedTiers roster={team.roster} />
    </main>
  );
}
