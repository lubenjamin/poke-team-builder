import { apiFetch } from "./client";
import type { Move, MoveDetail } from "../types/move";

export function fetchAllMoves(): Promise<Move[]> {
  return apiFetch<Move[]>("/api/moves", { withClientId: false });
}

export function fetchMove(idOrName: string): Promise<MoveDetail> {
  return apiFetch<MoveDetail>(`/api/moves/${idOrName}`, { withClientId: false });
}
