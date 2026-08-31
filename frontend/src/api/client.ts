import { getClientId } from "../hooks/useClientId";
import { getInternalSecret } from "../hooks/useInternalSecret";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  withClientId?: boolean;
  /** Attaches X-Internal-Secret from sessionStorage (see useInternalSecret)
   * — for the /dev-tools page's calls to the secret-gated /api/internal/*
   * routes. */
  withInternalSecret?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, withClientId = true, withInternalSecret = false } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (withClientId) headers["X-Client-Id"] = getClientId();
  if (withInternalSecret) {
    const secret = getInternalSecret();
    if (secret) headers["X-Internal-Secret"] = secret;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new ApiError(response.status, detail.detail ?? response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
