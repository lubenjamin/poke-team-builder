import { apiFetch } from "./client";
import type { Team, TeamDetail } from "../types/team";

export interface RosterSlotInput {
  pokemon_id: number;
  move_ids: number[];
}

export function fetchTeams(): Promise<TeamDetail[]> {
  return apiFetch<TeamDetail[]>("/api/teams");
}

export function createTeam(name: string, description: string | null = null): Promise<Team> {
  return apiFetch<Team>("/api/teams", { method: "POST", body: { name, description } });
}

export function fetchTeam(teamId: number): Promise<TeamDetail> {
  return apiFetch<TeamDetail>(`/api/teams/${teamId}`);
}

export function updateTeam(
  teamId: number,
  name: string,
  description: string | null,
): Promise<Team> {
  return apiFetch<Team>(`/api/teams/${teamId}`, {
    method: "PATCH",
    body: { name, description },
  });
}

export function deleteTeam(teamId: number): Promise<void> {
  return apiFetch<void>(`/api/teams/${teamId}`, { method: "DELETE" });
}

export function replaceRoster(teamId: number, slots: RosterSlotInput[]): Promise<TeamDetail> {
  return apiFetch<TeamDetail>(`/api/teams/${teamId}/roster`, {
    method: "PUT",
    body: { slots },
  });
}
