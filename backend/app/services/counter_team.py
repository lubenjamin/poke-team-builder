from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.pokemon import MoveRead, PokemonRead
from app.schemas.team import TeamPokemonRead

MAX_MOVES_PER_POKEMON = 4


def generate_random_team(db: Session, team_size: int) -> list[TeamPokemonRead]:
    """Placeholder counter-team generator: `team_size` random, distinct
    Pokemon (from the full open catalog — v1 has no format restrictions),
    each with up to 4 random moves from its own actual movepool.

    This exists to prove the submit -> generate -> display flow end-to-end.
    It knows nothing about the opponent team it's supposedly countering —
    real matchup-aware logic (types/stats/movepool of the input team) is a
    later iteration.
    """
    # Walk the whole catalog in random order, keeping the first form seen per
    # species — same "one form per species" rule enforced on saved rosters —
    # rather than a plain random LIMIT, which could land on e.g. both base
    # Rotom and Rotom-Wash by chance.
    shuffled = list(
        db.scalars(
            select(Pokemon)
            .options(selectinload(Pokemon.species))
            .order_by(func.random())
        )
    )
    candidates: list[Pokemon] = []
    seen_species: set[int] = set()
    for pokemon in shuffled:
        if pokemon.species_id in seen_species:
            continue
        candidates.append(pokemon)
        seen_species.add(pokemon.species_id)
        if len(candidates) >= team_size:
            break

    roster: list[TeamPokemonRead] = []
    for slot, pokemon in enumerate(candidates):
        move_ids = list(
            db.scalars(
                select(PokemonMovepool.move_id)
                .where(PokemonMovepool.pokemon_id == pokemon.id)
                .order_by(func.random())
                .limit(MAX_MOVES_PER_POKEMON)
            )
        )
        moves = list(db.scalars(select(Move).where(Move.id.in_(move_ids)))) if move_ids else []

        roster.append(
            TeamPokemonRead(
                slot=slot,
                pokemon=PokemonRead.model_validate(pokemon),
                moves=[MoveRead.model_validate(m) for m in moves],
            )
        )

    return roster
