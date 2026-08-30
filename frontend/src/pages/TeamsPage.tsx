import { useCallback, useEffect, useState } from "react";
import { deleteTeam, fetchTeams } from "../api/teams";
import { PageHero } from "../components/PageHero";
import { TeamBuilder } from "../components/TeamBuilder";
import { TeamList } from "../components/TeamList";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Team } from "../types/team";
import "./TeamsPage.css";

interface TeamsPageProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

export function TeamsPage({ catalog, moveCatalog }: TeamsPageProps) {
  useDocumentTitle("Teams");
  const [teams, setTeams] = useState<Team[]>([]);
  const [status, setStatus] = useState<"loading" | "error" | "ready">("loading");
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchTeams()
      .then((data) => {
        if (cancelled) return;
        setTeams(data);
        setStatus("ready");
        if (data.length > 0) setSelectedTeamId(data[0].id);
        else setIsCreatingNew(true);
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function confirmDiscardIfDirty(): boolean {
    if (!hasUnsavedChanges) return true;
    return confirm("You have unsaved changes to this team. Discard them?");
  }

  function handleSelect(id: number) {
    if (id === selectedTeamId && !isCreatingNew) return;
    if (!confirmDiscardIfDirty()) return;
    setIsCreatingNew(false);
    setSelectedTeamId(id);
    setHasUnsavedChanges(false);
  }

  function handleNewTeam() {
    if (isCreatingNew) return;
    if (!confirmDiscardIfDirty()) return;
    setIsCreatingNew(true);
    setHasUnsavedChanges(false);
  }

  async function handleDelete(teamId: number) {
    await deleteTeam(teamId);
    setTeams((prev) => prev.filter((t) => t.id !== teamId));
    if (selectedTeamId === teamId) {
      setSelectedTeamId(null);
      setHasUnsavedChanges(false);
    }
  }

  function handleSaved(team: Team) {
    setTeams((prev) => {
      const exists = prev.some((t) => t.id === team.id);
      return exists ? prev.map((t) => (t.id === team.id ? team : t)) : [...prev, team];
    });
    setIsCreatingNew(false);
    setSelectedTeamId(team.id);
    setHasUnsavedChanges(false);
  }

  const handleDirtyChange = useCallback((dirty: boolean) => setHasUnsavedChanges(dirty), []);

  if (status === "loading") return <p className="teams-page__message">Loading teams...</p>;
  if (status === "error") {
    return <p className="teams-page__message">Couldn't load teams. Is the backend running?</p>;
  }

  const activeTeamId = isCreatingNew ? null : selectedTeamId;

  return (
    <main>
      <PageHero
        title="Teams"
        description=""
      />
      <div className="teams-page__layout">
        <TeamList
          teams={teams}
          selectedId={selectedTeamId}
          isCreatingNew={isCreatingNew}
          onSelect={handleSelect}
          onNewTeam={handleNewTeam}
          onDelete={handleDelete}
        />
        {isCreatingNew || selectedTeamId !== null ? (
          <TeamBuilder
            key={isCreatingNew ? "draft" : selectedTeamId}
            teamId={activeTeamId}
            catalog={catalog}
            moveCatalog={moveCatalog}
            onSaved={handleSaved}
            onDirtyChange={handleDirtyChange}
          />
        ) : (
          <p className="teams-page__message">Create a team to get started.</p>
        )}
      </div>
    </main>
  );
}
