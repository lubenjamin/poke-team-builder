from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.roster_validation import validate_roster_slots
from app.schemas.team import CounterTeamRequest, TeamPokemonRead
from app.services.counter_team import generate_random_team

router = APIRouter(prefix="/api", tags=["counter-team"])

# Algorithm intentionally deferred until the fundamental app is running end-to-end
# (open-ended/creative per the assignment — see CLAUDE.md §9). generate_counter_team
# below is a first pass (random, proves the flow) — services/counter_team.py is
# where real matchup-aware logic replaces it.

_NOT_IMPLEMENTED = "Counter-team generation for a saved team is not yet implemented"


@router.post("/teams/{team_id}/counter-team")
def generate_counter_team_for_saved_team(team_id: int) -> None:
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/counter-team", response_model=list[TeamPokemonRead])
def generate_counter_team(
    body: CounterTeamRequest, db: Session = Depends(get_db)
) -> list[TeamPokemonRead]:
    validate_roster_slots(db, body.slots)
    return generate_random_team(db, team_size=len(body.slots))
