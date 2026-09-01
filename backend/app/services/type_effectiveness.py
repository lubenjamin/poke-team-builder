from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TypeEffectiveness


def compute_type_effectiveness(db: Session, defender_types: list[str]) -> dict[str, float]:
    """Combined incoming-damage multiplier per attacking type, for a Pokemon
    with 1-2 defending types. Dual-typed rows are combined by multiplying —
    e.g. Rock is 2x vs Ice and 2x vs Flying, so an Ice/Flying Pokemon takes
    4x from Rock."""
    rows = db.execute(
        select(TypeEffectiveness.attacking_type, TypeEffectiveness.multiplier).where(
            TypeEffectiveness.defending_type.in_(defender_types)
        )
    ).all()

    combined: dict[str, float] = {}
    for attacking_type, multiplier in rows:
        combined[attacking_type] = combined.get(attacking_type, 1.0) * multiplier
    return combined


def fetch_full_type_matrix(db: Session) -> dict[str, dict[str, float]]:
    """The full 18x18 type matchup chart as {attacking_type: {defending_type:
    multiplier}} — unlike compute_type_effectiveness (which combines this for
    one Pokemon's 1-2 defending types server-side), this hands back the whole
    chart for callers that need to evaluate many attacker/defender pairs
    in-memory: the frontend's team details page (defense matrix, damage-dealt
    figure) via GET /api/types/effectiveness, and the counter-team generator's
    per-candidate scoring (score_candidate, select_moves_for_coverage)."""
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
