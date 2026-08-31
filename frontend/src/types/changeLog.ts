export interface ChangeLogEntry {
  id: number;
  pokemon_id: number;
  field_name: string;
  old_value: string;
  new_value: string;
  detected_at: string;
}

export interface MoveChangeLogEntry {
  id: number;
  move_id: number;
  field_name: string;
  old_value: string;
  new_value: string;
  detected_at: string;
}
