from fastapi import APIRouter, HTTPException

from app.schemas.team import RosterReplace

router = APIRouter(prefix="/api", tags=["counter-team"])

# Algorithm intentionally deferred until the fundamental app is running end-to-end
# (open-ended/creative per the assignment — see CLAUDE.md §9). These routes are
# wired into the app now so the frontend can integrate against a stable contract;
# services/counter_team.py will implement the generation logic.

_NOT_IMPLEMENTED = "Counter-team generation is not yet implemented"


@router.post("/teams/{team_id}/counter-team")
def generate_counter_team_for_saved_team(team_id: int) -> None:
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/counter-team")
def generate_counter_team(body: RosterReplace) -> None:
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
