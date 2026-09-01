POKEMON_STAT_FIELDS = [
    "hp",
    "attack",
    "defense",
    "special_attack",
    "special_defense",
    "speed",
]


def validate_pokemon(transformed: dict) -> tuple[bool, str | None]:
    """valid only if all six stat fields are present and
    non-negative integers, all-or-nothing. Identity/display fields are checked too,
    since a NOT NULL violation on write would crash the batch instead of failing
    closed on just that record."""
    if not transformed.get("id"):
        return False, "missing id"
    if not transformed.get("name"):
        return False, "missing name"
    if not transformed.get("sprite_url"):
        return False, "missing sprite_url"
    if not transformed.get("types"):
        return False, "missing types"
    if not transformed.get("species_id"):
        return False, "missing species_id"

    for field in POKEMON_STAT_FIELDS:
        value = transformed.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return False, f"invalid stat field '{field}': {value!r}"

    return True, None


def validate_species(transformed: dict) -> tuple[bool, str | None]:
    """A national dex entry (from /pokedex/national) is valid only if it resolves
    to a positive species id, a non-empty name, and a positive dex number.
    Applies the same fail-closed contract as validate_pokemon — every field here
    is NOT NULL on PokemonSpecies, so a bad entry must be rejected before write,
    not crash the sync."""
    species_id = transformed.get("id")
    if not isinstance(species_id, int) or isinstance(species_id, bool) or species_id <= 0:
        return False, f"invalid species id: {species_id!r}"

    name = transformed.get("name")
    if not isinstance(name, str) or not name:
        return False, f"invalid species name: {name!r}"

    dex_number = transformed.get("national_dex_number")
    if not isinstance(dex_number, int) or isinstance(dex_number, bool) or dex_number <= 0:
        return False, f"invalid national_dex_number: {dex_number!r}"

    return True, None


MOVE_NULLABLE_NON_NEGATIVE_FIELDS = ["power", "accuracy", "pp", "effect_chance"]

def validate_move(transformed: dict) -> tuple[bool, str | None]:
    """A move is valid only if it has a positive id, a non-empty name and type
    and damage_class, and a present (but possibly negative) priority.
    power/accuracy/pp/effect_chance are optional but must be non-negative when
    present."""
    move_id = transformed.get("id")
    if not isinstance(move_id, int) or isinstance(move_id, bool) or move_id <= 0:
        return False, f"invalid move id: {move_id!r}"

    name = transformed.get("name")
    if not isinstance(name, str) or not name:
        return False, f"invalid move name: {name!r}"

    move_type = transformed.get("type")
    if not isinstance(move_type, str) or not move_type:
        return False, f"invalid move type: {move_type!r}"

    damage_class = transformed.get("damage_class")
    if not isinstance(damage_class, str) or not damage_class:
        return False, f"invalid damage_class: {damage_class!r}"

    priority = transformed.get("priority")
    if not isinstance(priority, int) or isinstance(priority, bool):
        return False, f"invalid field 'priority': {priority!r}"

    for field in MOVE_NULLABLE_NON_NEGATIVE_FIELDS:
        value = transformed.get(field)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            return False, f"invalid field '{field}': {value!r}"

    return True, None


VALID_TYPE_MULTIPLIERS = {0.0, 0.5, 1.0, 2.0}


def validate_type_matchup(transformed: dict) -> tuple[bool, str | None]:
    """A single type-pair relation is valid only if both type names are
    non-empty strings and the multiplier is one PokeAPI actually uses. A lone
    relation is never 4x/0.25x — those only emerge from combining two
    relations for a dual-typed Pokemon at query time (see
    services/type_effectiveness.py)."""
    attacking_type = transformed.get("attacking_type")
    if not isinstance(attacking_type, str) or not attacking_type:
        return False, f"invalid attacking_type: {attacking_type!r}"

    defending_type = transformed.get("defending_type")
    if not isinstance(defending_type, str) or not defending_type:
        return False, f"invalid defending_type: {defending_type!r}"

    multiplier = transformed.get("multiplier")
    if isinstance(multiplier, bool) or multiplier not in VALID_TYPE_MULTIPLIERS:
        return False, f"invalid multiplier: {multiplier!r}"

    return True, None
