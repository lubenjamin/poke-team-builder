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
