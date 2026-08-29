from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChangeLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pokemon_id: int
    field_name: str
    old_value: str
    new_value: str
    detected_at: datetime
