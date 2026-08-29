const STORAGE_KEY = "poke-team-builder:client-id";

export function getClientId(): string {
  let clientId = localStorage.getItem(STORAGE_KEY);
  if (!clientId) {
    clientId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, clientId);
  }
  return clientId;
}
