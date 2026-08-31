import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { deleteTeam, fetchTeams } from "../api/teams";
import { PageHero } from "../components/PageHero";
import { TeamList } from "../components/TeamList";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { TeamDetail } from "../types/team";
import "./TeamsPage.css";

export function TeamsPage() {
  useDocumentTitle("Teams");
  const navigate = useNavigate();
  const [teams, setTeams] = useState<TeamDetail[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;
    fetchTeams()
      .then((data) => {
        if (cancelled) return;
        setTeams(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDelete(teamId: number) {
    await deleteTeam(teamId);
    setTeams((prev) => prev.filter((t) => t.id !== teamId));
  }

  if (status === "loading") return <p className="teams-page__message">Loading teams...</p>;
  if (status === "error") {
    return <p className="teams-page__message">Couldn't load teams. Is the backend running?</p>;
  }

  return (
    <main>
      <PageHero title="Teams" description="" />
      <div className="teams-page__layout">
        <TeamList
          teams={teams}
          onSelect={(id) => navigate(`/teams/${id}`)}
          onNewTeam={() => navigate("/teams/new")}
          onDelete={handleDelete}
        />
      </div>
    </main>
  );
}
