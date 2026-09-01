from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.type_effectiveness import fetch_full_type_matrix

router = APIRouter(prefix="/api/types", tags=["types"])


@router.get("/effectiveness", response_model=dict[str, dict[str, float]])
def get_type_effectiveness_matrix(db: Session = Depends(get_db)) -> dict[str, dict[str, float]]:
    """The full 18x18 type matchup chart — the client uses this to compute
    defense *and* offense for every member of a team at once (the team
    details page's defense matrix and damage-dealt figure)."""
    return fetch_full_type_matrix(db)
