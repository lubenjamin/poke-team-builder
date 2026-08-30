import { apiFetch } from "./client";
import type { RosterSlotInput } from "./teams";
import type { TeamPokemonSlot } from "../types/team";

export function generateCounterTeam(slots: RosterSlotInput[]): Promise<TeamPokemonSlot[]> {
  return apiFetch<TeamPokemonSlot[]>("/api/counter-team", {
    method: "POST",
    body: { slots },
    withClientId: false,
  });
}
