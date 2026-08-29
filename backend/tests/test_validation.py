from app.services.validation import validate_pokemon, validate_species

VALID = {
    "id": 1,
    "name": "bulbasaur",
    "species_id": 1,
    "sprite_url": "https://example.com/1.png",
    "types": ["grass", "poison"],
    "hp": 45,
    "attack": 49,
    "defense": 49,
    "special_attack": 65,
    "special_defense": 65,
    "speed": 45,
}


def test_valid_pokemon_passes() -> None:
    is_valid, reason = validate_pokemon(VALID)
    assert is_valid is True
    assert reason is None


def test_missing_stat_field_rejected() -> None:
    payload = {**VALID, "speed": None}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "speed" in reason


def test_negative_stat_rejected() -> None:
    payload = {**VALID, "attack": -1}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "attack" in reason


def test_non_integer_stat_rejected() -> None:
    payload = {**VALID, "defense": "49"}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "defense" in reason


def test_bool_stat_rejected() -> None:
    # bool is technically an int subclass in Python; must not slip through
    payload = {**VALID, "hp": True}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "hp" in reason


def test_missing_name_rejected() -> None:
    payload = {**VALID, "name": None}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "name" in reason


def test_missing_species_id_rejected() -> None:
    payload = {**VALID, "species_id": None}
    is_valid, reason = validate_pokemon(payload)
    assert is_valid is False
    assert "species_id" in reason


VALID_SPECIES = {"id": 479, "name": "rotom", "national_dex_number": 479}


def test_valid_species_passes() -> None:
    is_valid, reason = validate_species(VALID_SPECIES)
    assert is_valid is True
    assert reason is None


def test_species_missing_id_rejected() -> None:
    payload = {**VALID_SPECIES, "id": None}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
    assert "id" in reason


def test_species_zero_id_rejected() -> None:
    payload = {**VALID_SPECIES, "id": 0}
    is_valid, reason = validate_species(payload)
    assert is_valid is False


def test_species_missing_name_rejected() -> None:
    payload = {**VALID_SPECIES, "name": None}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
    assert "name" in reason


def test_species_empty_name_rejected() -> None:
    payload = {**VALID_SPECIES, "name": ""}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
    assert "name" in reason


def test_species_missing_dex_number_rejected() -> None:
    payload = {**VALID_SPECIES, "national_dex_number": None}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
    assert "national_dex_number" in reason


def test_species_negative_dex_number_rejected() -> None:
    payload = {**VALID_SPECIES, "national_dex_number": -5}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
    assert "national_dex_number" in reason


def test_species_bool_id_rejected() -> None:
    payload = {**VALID_SPECIES, "id": True}
    is_valid, reason = validate_species(payload)
    assert is_valid is False
