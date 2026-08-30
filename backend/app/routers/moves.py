from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.pokemon import MoveRead, PokemonRead

router = APIRouter(prefix="/api/moves", tags=["moves"])


class MoveDetail(MoveRead):
    learnable_by: list[PokemonRead]


def _get_move_by_id_or_name(id_or_name: str, db: Session) -> Move | None:
    try:
        move_id = int(id_or_name)
    except ValueError:
        return db.scalars(select(Move).where(Move.name == id_or_name)).first()
    return db.get(Move, move_id)


@router.get("", response_model=list[MoveRead])
def list_moves(db: Session = Depends(get_db)) -> list[Move]:
    return list(db.scalars(select(Move).order_by(Move.id)))


@router.get("/{id_or_name}", response_model=MoveDetail)
def get_move(id_or_name: str, db: Session = Depends(get_db)) -> MoveDetail:
    move = _get_move_by_id_or_name(id_or_name, db)
    if move is None:
        raise HTTPException(status_code=404, detail="Move not found")

    stmt = (
        select(Pokemon)
        .join(PokemonMovepool, PokemonMovepool.pokemon_id == Pokemon.id)
        .where(PokemonMovepool.move_id == move.id)
        .options(selectinload(Pokemon.species))
        .order_by(Pokemon.id)
    )
    learnable_by = list(db.scalars(stmt))

    return MoveDetail(
        **MoveRead.model_validate(move).model_dump(),
        learnable_by=[PokemonRead.model_validate(p) for p in learnable_by],
    )
