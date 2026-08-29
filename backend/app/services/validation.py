STAT_FIELDS = [
    "hp",
    "attack",
    "defense",
    "special_attack",
    "special_defense",
    "speed",
]


def validate_pokemon(transformed: dict) -> tuple[bool, str | None]:
    """v1 rule (CLAUDE.md §6): valid only if all six stat fields are present and
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

    for field in STAT_FIELDS:
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
