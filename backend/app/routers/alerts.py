from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_client_id
from app.models import Alert
from app.schemas.alert import AlertRead

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Alerts are filtered by *current* team membership at read time, not just
# written once and left static — see docs/schema.md for the rationale.
_ACTIVE_ALERTS_SQL = text(
    """
    SELECT alerts.*
    FROM alerts
    JOIN team_pokemon
      ON team_pokemon.team_id = alerts.team_id
      AND team_pokemon.pokemon_id = alerts.pokemon_id
    WHERE alerts.client_id = :client_id
      AND alerts.dismissed = false
      AND alerts.created_at > now() - interval '7 days'
    ORDER BY alerts.created_at DESC
    """
)


@router.get("", response_model=list[AlertRead])
def list_active_alerts(
    client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(_ACTIVE_ALERTS_SQL, {"client_id": client_id}).mappings().all()
    return [dict(row) for row in rows]


@router.post("/{alert_id}/dismiss", status_code=204)
def dismiss_alert(
    alert_id: int, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> None:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.client_id != client_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.dismissed = True
    db.commit()
