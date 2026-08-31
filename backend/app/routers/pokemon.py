from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Move, Pokemon, PokemonChangeLog, PokemonMovepool
from app.schemas.pokemon import MoveRead, PokemonCatalogVersion, PokemonDetail, PokemonRead
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


@router.get("/version", response_model=PokemonCatalogVersion)
def get_pokemon_catalog_version(db: Session = Depends(get_db)) -> PokemonCatalogVersion:
    """Cheap freshness check for a client-side catalog cache — the max
    detected_at across pokemon_change_log only moves when a scan actually
    found a change (unlike last_fetched_at, which touches on every scan
    regardless of outcome). A client compares this against whatever it
    cached alongside its stored copy of the full catalog, and only re-fetches
    the /api/pokemon payload if it doesn't match.

    Registered before /{id_or_name} below — it must be, since that route
    would otherwise swallow "version" as a literal id_or_name lookup."""
    version = db.scalar(select(func.max(PokemonChangeLog.detected_at)))
    return PokemonCatalogVersion(version=version.isoformat() if version else None)


@router.get("/movepool", response_model=dict[int, list[int]])
def get_pokemon_movepool_map(db: Session = Depends(get_db)) -> dict[int, list[int]]:
    """{pokemon_id: [learnable move ids]} for the whole catalog — split out
    of the main /api/pokemon list (which every page pays for, Pokedex
    included) since only the team builder's move picker actually needs this.
    Fetched lazily, once, by usePokemonMovepool on the frontend — only when
    a team-builder-related page actually mounts it, not on every app load.

    Registered before /{id_or_name} for the same reason /version is."""
    result: dict[int, list[int]] = {}
    for pokemon_id, move_id in db.execute(
        select(PokemonMovepool.pokemon_id, PokemonMovepool.move_id)
    ).all():
        result.setdefault(pokemon_id, []).append(move_id)
    return result


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
