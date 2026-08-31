import { apiFetch } from "./client";
import type { ChangeLogEntry, MoveChangeLogEntry } from "../types/changeLog";

export function fetchChanges(limit = 100): Promise<ChangeLogEntry[]> {
  return apiFetch<ChangeLogEntry[]>(`/api/changes?limit=${limit}`, { withClientId: false });
}

export function fetchMoveChanges(limit = 100): Promise<MoveChangeLogEntry[]> {
  return apiFetch<MoveChangeLogEntry[]>(`/api/changes/moves?limit=${limit}`, {
    withClientId: false,
  });
}
