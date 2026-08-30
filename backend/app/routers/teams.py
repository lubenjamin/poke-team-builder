from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import get_client_id
from app.models import Move, Pokemon, PokemonMovepool, Team, TeamPokemon, TeamPokemonMove
from app.schemas.team import RosterReplace, TeamCreate, TeamDetail, TeamRead, TeamUpdate

router = APIRouter(prefix="/api/teams", tags=["teams"])


def _get_owned_team(team_id: int, client_id: str, db: Session) -> Team:
    team = db.get(Team, team_id)
    if team is None or team.client_id != client_id:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("", response_model=list[TeamRead])
def list_teams(
    client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> list[Team]:
    stmt = select(Team).where(Team.client_id == client_id).order_by(Team.created_at)
    return list(db.scalars(stmt))


@router.post("", response_model=TeamRead, status_code=201)
def create_team(
    body: TeamCreate, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> Team:
    team = Team(client_id=client_id, name=body.name, description=body.description)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamDetail)
def get_team(
    team_id: int, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> Team:
    stmt = (
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.roster).selectinload(TeamPokemon.pokemon).selectinload(
                Pokemon.species
            ),
            selectinload(Team.roster).selectinload(TeamPokemon.move_links).selectinload(
                TeamPokemonMove.move
            ),
        )
    )
    team = db.scalars(stmt).first()
    if team is None or team.client_id != client_id:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.patch("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: int,
    body: TeamUpdate,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> Team:
    team = _get_owned_team(team_id, client_id, db)
    team.name = body.name
    team.description = body.description
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int, client_id: str = Depends(get_client_id), db: Session = Depends(get_db)
) -> None:
    team = _get_owned_team(team_id, client_id, db)
    db.delete(team)
    db.commit()


@router.put("/{team_id}/roster", response_model=TeamDetail)
def replace_roster(
    team_id: int,
    body: RosterReplace,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
) -> Team:
    team = _get_owned_team(team_id, client_id, db)

    pokemon_ids = [slot.pokemon_id for slot in body.slots]
    if pokemon_ids:
        found_pokemon_ids = set(db.scalars(select(Pokemon.id).where(Pokemon.id.in_(pokemon_ids))))
        missing_pokemon = set(pokemon_ids) - found_pokemon_ids
        if missing_pokemon:
            raise HTTPException(
                status_code=422, detail=f"Unknown pokemon_ids: {sorted(missing_pokemon)}"
            )

    all_move_ids = {move_id for slot in body.slots for move_id in slot.move_ids}
    if all_move_ids:
        found_move_ids = set(db.scalars(select(Move.id).where(Move.id.in_(all_move_ids))))
        missing_moves = all_move_ids - found_move_ids
        if missing_moves:
            raise HTTPException(
                status_code=422, detail=f"Unknown move_ids: {sorted(missing_moves)}"
            )

    for slot in body.slots:
        if not slot.move_ids:
            continue
        learnable = set(
            db.scalars(
                select(PokemonMovepool.move_id).where(
                    PokemonMovepool.pokemon_id == slot.pokemon_id,
                    PokemonMovepool.move_id.in_(slot.move_ids),
                )
            )
        )
        not_learnable = set(slot.move_ids) - learnable
        if not_learnable:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Pokemon {slot.pokemon_id} cannot learn move_ids: {sorted(not_learnable)}"
                ),
            )

    team.roster.clear()
    db.flush()
    for slot_index, slot_input in enumerate(body.slots):
        team_pokemon = TeamPokemon(pokemon_id=slot_input.pokemon_id, slot=slot_index)
        for move_slot_index, move_id in enumerate(slot_input.move_ids):
            team_pokemon.move_links.append(
                TeamPokemonMove(move_id=move_id, slot=move_slot_index)
            )
        team.roster.append(team_pokemon)
    db.commit()
    db.refresh(team)
    return team
