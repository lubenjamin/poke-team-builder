from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    pokemon_id: int
    move_id: int | None
    pokemon_change_log_id: int | None
    move_change_log_id: int | None
    message: str
    created_at: datetime
