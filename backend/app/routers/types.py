from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TypeEffectiveness

router = APIRouter(prefix="/api/types", tags=["types"])


@router.get("/effectiveness", response_model=dict[str, dict[str, float]])
def get_type_effectiveness_matrix(db: Session = Depends(get_db)) -> dict[str, dict[str, float]]:
    """The full 18x18 type matchup chart as {attacking_type: {defending_type:
    multiplier}} — unlike compute_type_effectiveness (which combines this for
    one Pokemon's 1-2 defending types server-side), this hands the whole
    chart to the client so it can compute defense *and* offense for every
    member of a team at once (the team details page's defense matrix and
    damage-dealt figure)."""
    result: dict[str, dict[str, float]] = {}
    for attacking_type, defending_type, multiplier in db.execute(
        select(
            TypeEffectiveness.attacking_type,
            TypeEffectiveness.defending_type,
            TypeEffectiveness.multiplier,
        )
    ).all():
        result.setdefault(attacking_type, {})[defending_type] = multiplier
    return result
