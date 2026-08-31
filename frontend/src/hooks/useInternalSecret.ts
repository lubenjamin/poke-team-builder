import { useState } from "react";

const STORAGE_KEY = "poke-team-builder:internal-secret";

/** Plain (non-hook) accessor for api/client.ts, which isn't a component and
 * can't call hooks — mirrors useClientId.ts's getClientId(). Session-scoped
 * (not localStorage) since this is a sensitive value that shouldn't outlive
 * the tab. */
export function getInternalSecret(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/** Reactive version for the /dev-tools page: lets the UI switch from "enter
 * secret" to the actual tools the moment one's entered, without a reload. */
export function useInternalSecret(): {
  secret: string | null;
  setSecret: (value: string) => void;
  clearSecret: () => void;
} {
  const [secret, setSecretState] = useState<string | null>(() => getInternalSecret());

  function setSecret(value: string) {
    try {
      sessionStorage.setItem(STORAGE_KEY, value);
    } catch {
      // Best-effort — if storage is unavailable the secret still works for
      // this render via state, it just won't survive a refresh.
    }
    setSecretState(value);
  }

  function clearSecret() {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setSecretState(null);
  }

  return { secret, setSecret, clearSecret };
}
