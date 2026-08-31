import { apiFetch } from "./client";
import type { Alert } from "../types/alert";

export function fetchAlerts(): Promise<Alert[]> {
  return apiFetch<Alert[]>("/api/alerts");
}

export function dismissAlert(alertId: number): Promise<void> {
  return apiFetch<void>(`/api/alerts/${alertId}/dismiss`, { method: "POST" });
}
