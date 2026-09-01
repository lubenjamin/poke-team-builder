import { apiFetch } from "./client";
import type { RosterSlotInput } from "./teams";
import type { TeamDetail, TeamPokemonSlot } from "../types/team";

export function generateCounterTeam(slots: RosterSlotInput[]): Promise<TeamPokemonSlot[]> {
  return apiFetch<TeamPokemonSlot[]>("/api/counter-team", {
    method: "POST",
    body: { slots },
    withClientId: false,
  });
}

/** Preview a counter team for an already-saved team — same generator as
 * generateCounterTeam above, just sourcing the opponent roster from a
 * team_id server-side instead of a hand-built slots payload. */
export function generateCounterTeamForTeam(teamId: number): Promise<TeamPokemonSlot[]> {
  return apiFetch<TeamPokemonSlot[]>(`/api/teams/${teamId}/counter-team`, { method: "POST" });
}

/** One-click save: regenerates the same counter team and persists it as a
 * new team owned by this client. */
export function saveCounterTeamForTeam(teamId: number): Promise<TeamDetail> {
  return apiFetch<TeamDetail>(`/api/teams/${teamId}/counter-team/save`, { method: "POST" });
}
