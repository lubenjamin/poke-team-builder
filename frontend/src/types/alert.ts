export interface Alert {
  id: number;
  team_id: number;
  pokemon_id: number;
  move_id: number | null;
  pokemon_change_log_id: number | null;
  move_change_log_id: number | null;
  message: string;
  created_at: string;
}
