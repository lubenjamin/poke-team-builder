from pydantic import BaseModel, ConfigDict


class ScanResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scanned: int
    changed: int
    changes_logged: int
    alerts_created: int
    fetch_failed: int
