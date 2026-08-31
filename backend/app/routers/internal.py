from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_internal_secret
from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.dev_tools import MovepoolCorruption, MoveStatUpdate, PokemonStatUpdate
from app.schemas.scan import ScanResultRead
from app.services.change_detection import (
    DEFAULT_MAX_WORKERS,
    scan_all_moves_for_changes,
    scan_all_pokemon_for_changes,
)

router = APIRouter(
    prefix="/api/internal", tags=["internal"], dependencies=[Depends(require_internal_secret)]
)

# Every route on this router is secret-gated (see the router-level
# dependency above) — it backs both the GitHub Actions cron (the real
# production trigger) and the /dev-tools page (same category of privileged
# action, same gate: prompt for the secret once, store it client-side).


@router.post("/scan-pokemon", response_model=ScanResultRead)
def scan_pokemon(
    limit: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    db: Session = Depends(get_db),
) -> ScanResultRead:
    """`limit` caps how many cached Pokemon are re-checked — useful for a
    fast demo run instead of the full catalog. `max_workers` bounds how many
    PokeAPI fetches run concurrently."""
    return scan_all_pokemon_for_changes(db, limit=limit, max_workers=max_workers)


@router.post("/scan-moves", response_model=ScanResultRead)
def scan_moves(
    limit: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    db: Session = Depends(get_db),
) -> ScanResultRead:
    """Move counterpart to /scan-pokemon — independently triggerable/
    schedulable, since Pokemon and move data have different real-world
    PokeAPI update cadences."""
    return scan_all_moves_for_changes(db, limit=limit, max_workers=max_workers)


@router.patch("/pokemon/{pokemon_id}")
def debug_set_pokemon_stat(
    pokemon_id: int, body: PokemonStatUpdate, db: Session = Depends(get_db)
) -> dict[str, str]:
    pokemon = db.get(Pokemon, pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    setattr(pokemon, body.field, body.value)
    db.commit()
    return {"status": "ok"}


@router.patch("/moves/{move_id}")
def debug_set_move_stat(
    move_id: int, body: MoveStatUpdate, db: Session = Depends(get_db)
) -> dict[str, str]:
    move = db.get(Move, move_id)
    if move is None:
        raise HTTPException(status_code=404, detail="Move not found")
    setattr(move, body.field, body.value)
    db.commit()
    return {"status": "ok"}


@router.post("/pokemon/{pokemon_id}/movepool")
def debug_add_movepool_entry(
    pokemon_id: int, body: MovepoolCorruption, db: Session = Depends(get_db)
) -> dict[str, str]:
    pokemon = db.get(Pokemon, pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    move = db.get(Move, body.move_id)
    if move is None:
        raise HTTPException(status_code=404, detail="Move not found")

    existing = (
        db.query(PokemonMovepool)
        .filter(
            PokemonMovepool.pokemon_id == pokemon_id, PokemonMovepool.move_id == body.move_id
        )
        .first()
    )
    if existing is None:
        db.add(PokemonMovepool(pokemon_id=pokemon_id, move_id=body.move_id))
        db.commit()
    return {"status": "ok"}
