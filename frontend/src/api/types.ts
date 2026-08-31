import { apiFetch } from "./client";

export function fetchTypeEffectiveness(): Promise<Record<string, Record<string, number>>> {
  return apiFetch<Record<string, Record<string, number>>>("/api/types/effectiveness", {
    withClientId: false,
  });
}
