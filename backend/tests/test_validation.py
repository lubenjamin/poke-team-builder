from app.services.validation import (
    validate_move,
    validate_pokemon,
    validate_species,
    validate_type_matchup,
)

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


VALID_MOVE = {
    "id": 1,
    "name": "pound",
    "type": "normal",
    "damage_class": "physical",
    "power": 40,
    "accuracy": 100,
    "pp": 35,
    "priority": 0,
    "effect_chance": None,
}


def test_valid_move_passes() -> None:
    is_valid, reason = validate_move(VALID_MOVE)
    assert is_valid is True
    assert reason is None


def test_move_null_power_is_valid() -> None:
    # status moves (e.g. Swords Dance) legitimately have no power
    payload = {**VALID_MOVE, "power": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is True


def test_move_null_accuracy_is_valid() -> None:
    # guaranteed-hit moves (e.g. Swift) legitimately have no accuracy
    payload = {**VALID_MOVE, "accuracy": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is True


def test_move_null_effect_chance_is_valid() -> None:
    payload = {**VALID_MOVE, "effect_chance": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is True


def test_move_negative_power_rejected() -> None:
    payload = {**VALID_MOVE, "power": -10}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "power" in reason


def test_move_null_pp_is_valid() -> None:
    # Z-Moves/Max Moves (PokeAPI ids 10001+) have no pp of their own — they
    # inherit it from the move they're derived from
    payload = {**VALID_MOVE, "pp": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is True


def test_move_negative_pp_rejected() -> None:
    payload = {**VALID_MOVE, "pp": -1}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "pp" in reason


def test_move_negative_priority_is_valid() -> None:
    # priority is signed — e.g. Trick Room is -7, Counter is -5
    payload = {**VALID_MOVE, "priority": -7}
    is_valid, reason = validate_move(payload)
    assert is_valid is True


def test_move_missing_priority_rejected() -> None:
    payload = {**VALID_MOVE, "priority": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "priority" in reason


def test_move_missing_type_rejected() -> None:
    payload = {**VALID_MOVE, "type": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "type" in reason


def test_move_missing_damage_class_rejected() -> None:
    payload = {**VALID_MOVE, "damage_class": None}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "damage_class" in reason


def test_move_missing_name_rejected() -> None:
    payload = {**VALID_MOVE, "name": ""}
    is_valid, reason = validate_move(payload)
    assert is_valid is False
    assert "name" in reason


def test_move_zero_id_rejected() -> None:
    payload = {**VALID_MOVE, "id": 0}
    is_valid, reason = validate_move(payload)
    assert is_valid is False


VALID_TYPE_MATCHUP = {"attacking_type": "fire", "defending_type": "grass", "multiplier": 2.0}


def test_valid_type_matchup_passes() -> None:
    is_valid, reason = validate_type_matchup(VALID_TYPE_MATCHUP)
    assert is_valid is True
    assert reason is None


def test_type_matchup_neutral_multiplier_is_valid() -> None:
    payload = {**VALID_TYPE_MATCHUP, "multiplier": 1.0}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is True


def test_type_matchup_zero_multiplier_is_valid() -> None:
    payload = {**VALID_TYPE_MATCHUP, "multiplier": 0.0}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is True


def test_type_matchup_invalid_multiplier_rejected() -> None:
    # a single relation is never 4x -- that only emerges from combining two
    # relations for a dual-typed Pokemon at query time
    payload = {**VALID_TYPE_MATCHUP, "multiplier": 4.0}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is False
    assert "multiplier" in reason


def test_type_matchup_missing_attacking_type_rejected() -> None:
    payload = {**VALID_TYPE_MATCHUP, "attacking_type": None}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is False
    assert "attacking_type" in reason


def test_type_matchup_missing_defending_type_rejected() -> None:
    payload = {**VALID_TYPE_MATCHUP, "defending_type": ""}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is False
    assert "defending_type" in reason


def test_type_matchup_bool_multiplier_rejected() -> None:
    payload = {**VALID_TYPE_MATCHUP, "multiplier": True}
    is_valid, reason = validate_type_matchup(payload)
    assert is_valid is False
