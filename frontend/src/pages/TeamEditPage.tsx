import { useNavigate, useParams } from "react-router-dom";
import { TeamBuilder } from "../components/TeamBuilder";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import type { MoveCatalog } from "../hooks/useMoveCatalog";
import type { PokemonCatalog } from "../hooks/usePokemonCatalog";
import type { Team } from "../types/team";
import "./TeamEditPage.css";

interface TeamEditPageProps {
  catalog: PokemonCatalog;
  moveCatalog: MoveCatalog;
}

/** Thin wrapper around the untouched TeamBuilder/RosterEditor edit flow —
 * backs both /teams/new (teamId undefined -> null, create) and
 * /teams/:teamId/edit (edit). Owns navigation on save, replacing what
 * TeamsPage's local state used to do before teams got their own detail
 * route. */
export function TeamEditPage({ catalog, moveCatalog }: TeamEditPageProps) {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const isNew = !teamId || teamId === "new";

  useDocumentTitle(isNew ? "New Team" : "Edit Team");

  function handleSaved(team: Team) {
    navigate(`/teams/${team.id}`);
  }

  return (
    <main className="team-edit-page">
      <TeamBuilder
        key={isNew ? "new" : teamId}
        teamId={isNew ? null : Number(teamId)}
        catalog={catalog}
        moveCatalog={moveCatalog}
        onSaved={handleSaved}
        onDirtyChange={() => {}}
      />
    </main>
  );
}
