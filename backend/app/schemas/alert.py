from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    pokemon_id: int
    change_log_id: int
    message: str
    created_at: datetime
