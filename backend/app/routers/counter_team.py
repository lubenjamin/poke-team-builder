from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_client_id
from app.models import Move, Pokemon, Team, TeamPokemon, TeamPokemonMove
from app.routers.roster_validation import validate_roster_slots
from app.routers.teams import fetch_owned_team_with_roster
from app.schemas.team import CounterTeamRequest, TeamDetail, TeamPokemonRead
from app.services.counter_team import BattleRosterSlot, generate_matchup_counter_team

router = APIRouter(prefix="/api", tags=["counter-team"])


def _generate_counter_team_for_saved_team(
    team_id: int, client_id: str, db: Session
) -> tuple[Team, list[TeamPokemonRead]]:
    """Loads a saved team (ownership-checked) and runs the matchup-aware
    generator against its roster — shared by the read-only preview route
    and the save route below, so "generate" and "generate, then persist"
    can't drift into computing two different teams."""
    source_team = fetch_owned_team_with_roster(team_id, client_id, db)
    if not source_team.roster:
        raise HTTPException(status_code=400, detail="Team has no Pokemon to counter")

    opponent_roster = [
        BattleRosterSlot(pokemon=team_pokemon.pokemon, moves=team_pokemon.moves)
        for team_pokemon in source_team.roster
    ]
    generated = generate_matchup_counter_team(db, opponent_roster, team_size=len(opponent_roster))
    return source_team, generated


@router.post("/teams/{team_id}/counter-team", response_model=list[TeamPokemonRead])
def generate_counter_team_for_saved_team(
    team_id: int, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> list[TeamPokemonRead]:
    _source_team, generated = _generate_counter_team_for_saved_team(team_id, client_id, db)
    return generated


@router.post("/teams/{team_id}/counter-team/save", response_model=TeamDetail, status_code=201)
def save_counter_team_for_saved_team(
    team_id: int, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> Team:
    """One-click save: generate a counter team for team_id (same generator
    and result the preview route above would show) and persist it as a new
    team owned by the same client, instead of making the frontend re-submit
    the generated roster back through PUT .../roster itself."""
    source_team, generated = _generate_counter_team_for_saved_team(team_id, client_id, db)

    new_team = Team(client_id=client_id, name=f"Counter to {source_team.name}")
    for team_pokemon_read in generated:
        team_pokemon = TeamPokemon(
            pokemon_id=team_pokemon_read.pokemon.id, slot=team_pokemon_read.slot
        )
        for move_slot, move in enumerate(team_pokemon_read.moves):
            team_pokemon.move_links.append(TeamPokemonMove(move_id=move.id, slot=move_slot))
        new_team.roster.append(team_pokemon)

    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team


def _build_opponent_roster(db: Session, body: CounterTeamRequest) -> list[BattleRosterSlot]:
    pokemon_ids = [slot.pokemon_id for slot in body.slots]
    pokemon_by_id = {
        p.id: p for p in db.scalars(select(Pokemon).where(Pokemon.id.in_(pokemon_ids)))
    }

    all_move_ids = {move_id for slot in body.slots for move_id in slot.move_ids}
    move_by_id = (
        {m.id: m for m in db.scalars(select(Move).where(Move.id.in_(all_move_ids)))}
        if all_move_ids
        else {}
    )

    return [
        BattleRosterSlot(
            pokemon=pokemon_by_id[slot.pokemon_id],
            moves=[move_by_id[move_id] for move_id in slot.move_ids],
        )
        for slot in body.slots
    ]


@router.post("/counter-team", response_model=list[TeamPokemonRead])
def generate_counter_team(
    body: CounterTeamRequest, db: Session = Depends(get_db)
) -> list[TeamPokemonRead]:
    validate_roster_slots(db, body.slots)
    opponent_roster = _build_opponent_roster(db, body)
    return generate_matchup_counter_team(db, opponent_roster, team_size=len(body.slots))
