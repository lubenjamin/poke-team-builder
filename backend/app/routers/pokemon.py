from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Pokemon
from app.schemas.pokemon import PokemonRead

router = APIRouter(prefix="/api/pokemon", tags=["pokemon"])


@router.get("", response_model=list[PokemonRead])
def list_pokemon(db: Session = Depends(get_db)) -> list[Pokemon]:
    stmt = select(Pokemon).options(selectinload(Pokemon.species)).order_by(Pokemon.id)
    return list(db.scalars(stmt))


@router.get("/{pokemon_id}", response_model=PokemonRead)
def get_pokemon(pokemon_id: int, db: Session = Depends(get_db)) -> Pokemon:
    stmt = (
        select(Pokemon).options(selectinload(Pokemon.species)).where(Pokemon.id == pokemon_id)
    )
    pokemon = db.scalars(stmt).first()
    if pokemon is None:
        raise HTTPException(status_code=404, detail="Pokemon not found")
    return pokemon
