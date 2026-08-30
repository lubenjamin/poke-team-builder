from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.pokemon import MoveRead, PokemonDetail, PokemonRead
from app.services.type_effectiveness import compute_type_effectiveness

router = APIRouter(prefix="/api/pokemon", tags=["pokemon"])


def _get_pokemon_by_id_or_name(id_or_name: str, db: Session) -> Pokemon | None:
    stmt = select(Pokemon).options(selectinload(Pokemon.species))
    try:
        pokemon_id = int(id_or_name)
    except ValueError:
        stmt = stmt.where(Pokemon.name == id_or_name)
    else:
        stmt = stmt.where(Pokemon.id == pokemon_id)
    return db.scalars(stmt).first()


@router.get("", response_model=list[PokemonRead])
def list_pokemon(db: Session = Depends(get_db)) -> list[Pokemon]:
    stmt = select(Pokemon).options(selectinload(Pokemon.species)).order_by(Pokemon.id)
    return list(db.scalars(stmt))


@router.get("/{id_or_name}", response_model=PokemonDetail)
def get_pokemon(id_or_name: str, db: Session = Depends(get_db)) -> PokemonDetail:
    pokemon = _get_pokemon_by_id_or_name(id_or_name, db)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    stmt = (
        select(Move)
        .join(PokemonMovepool, PokemonMovepool.move_id == Move.id)
        .where(PokemonMovepool.pokemon_id == pokemon.id)
        .order_by(Move.name)
    )
    learnable_moves = list(db.scalars(stmt))
    type_effectiveness = compute_type_effectiveness(db, pokemon.types)

    return PokemonDetail(
        **PokemonRead.model_validate(pokemon).model_dump(),
        learnable_moves=[MoveRead.model_validate(m) for m in learnable_moves],
        type_effectiveness=type_effectiveness,
    )
