from collections import Counter

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.team import RosterSlotInput


def _raise_if_missing(requested: set[int], available: set[int], message: str) -> None:
    """Shared shape for every "these ids must all be in that set" check
    below — diff the two sets and raise a 422 naming exactly which ids
    failed. `message` is just the prefix (e.g. "Unknown move_ids")."""
    missing = requested - available
    if missing:
        raise HTTPException(status_code=422, detail=f"{message}: {sorted(missing)}")


def validate_roster_slots(db: Session, slots: list[RosterSlotInput]) -> None:
    """Raises HTTPException(422) if any pokemon_id/move_id doesn't exist, a
    pokemon_id is a battle-only form, two slots share a species, or a move
    isn't actually in that Pokemon's movepool. Shared by teams.replace_roster
    and counter_team.generate_counter_team — both accept the same
    {pokemon_id, move_ids}[] shape and need the same checks, including for
    the opponent roster you submit to be countered: that's also describing
    a team, so the same legality rules apply to it."""
    pokemon_ids = [slot.pokemon_id for slot in slots]
    if pokemon_ids:
        found_pokemon_ids = set(db.scalars(select(Pokemon.id).where(Pokemon.id.in_(pokemon_ids))))
        _raise_if_missing(set(pokemon_ids), found_pokemon_ids, "Unknown pokemon_ids")

        pokemon_rows = db.execute(
            select(Pokemon.id, Pokemon.species_id, Pokemon.is_battle_only).where(
                Pokemon.id.in_(pokemon_ids)
            )
        ).all()

        battle_only_ids = sorted(
            pokemon_id for pokemon_id, _species_id, is_battle_only in pokemon_rows if is_battle_only
        )
        if battle_only_ids:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Battle-only forms (e.g. Mega Evolutions) can't be added to a team — "
                    f"pokemon_ids: {battle_only_ids}"
                ),
            )

        species_counts = Counter(species_id for _pokemon_id, species_id, _is_battle_only in pokemon_rows)
        duplicate_species = sorted(
            species_id for species_id, count in species_counts.items() if count > 1
        )
        if duplicate_species:
            raise HTTPException(
                status_code=422,
                detail=(
                    "A team can only have one form per species — duplicate species_ids: "
                    f"{duplicate_species}"
                ),
            )

    all_move_ids = {move_id for slot in slots for move_id in slot.move_ids}
    if all_move_ids:
        found_move_ids = set(db.scalars(select(Move.id).where(Move.id.in_(all_move_ids))))
        _raise_if_missing(all_move_ids, found_move_ids, "Unknown move_ids")

    for slot in slots:
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
        _raise_if_missing(
            set(slot.move_ids), learnable, f"Pokemon {slot.pokemon_id} cannot learn move_ids"
        )
