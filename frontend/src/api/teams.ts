import { apiFetch } from "./client";
import type { Team, TeamDetail } from "../types/team";

export function fetchTeams(): Promise<Team[]> {
  return apiFetch<Team[]>("/api/teams");
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

export function replaceRoster(teamId: number, pokemonIds: number[]): Promise<TeamDetail> {
  return apiFetch<TeamDetail>(`/api/teams/${teamId}/roster`, {
    method: "PUT",
    body: { pokemon_ids: pokemonIds },
  });
}
