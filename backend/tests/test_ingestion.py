from app.services.ingestion import (
    transform_move,
    transform_pokemon,
    transform_species_entry,
    transform_type_matchups,
)

RAW_BULBASAUR = {
    "id": 1,
    "name": "bulbasaur",
    "is_default": True,
    "species": {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
    "types": [
        {"slot": 2, "type": {"name": "poison", "url": "..."}},
        {"slot": 1, "type": {"name": "grass", "url": "..."}},
    ],
    "moves": [
        {"move": {"name": "tackle", "url": "https://pokeapi.co/api/v2/move/33/"}},
        {"move": {"name": "growl", "url": "https://pokeapi.co/api/v2/move/45/"}},
    ],
    "stats": [
        {"base_stat": 45, "stat": {"name": "hp"}},
        {"base_stat": 49, "stat": {"name": "attack"}},
        {"base_stat": 49, "stat": {"name": "defense"}},
        {"base_stat": 65, "stat": {"name": "special-attack"}},
        {"base_stat": 65, "stat": {"name": "special-defense"}},
        {"base_stat": 45, "stat": {"name": "speed"}},
    ],
    "sprites": {
        "front_default": "https://example.com/sprites/1.png",
        "other": {
            "official-artwork": {"front_default": "https://example.com/artwork/1.png"}
        },
    },
}


def test_transform_orders_types_by_slot() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert result["types"] == ["grass", "poison"]


def test_transform_maps_stats() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert result["hp"] == 45
    assert result["attack"] == 49
    assert result["defense"] == 49
    assert result["special_attack"] == 65
    assert result["special_defense"] == 65
    assert result["speed"] == 45


def test_transform_prefers_official_artwork_sprite() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert result["sprite_url"] == "https://example.com/artwork/1.png"


def test_transform_falls_back_to_front_default_sprite() -> None:
    raw = {**RAW_BULBASAUR, "sprites": {"front_default": "https://example.com/sprites/1.png"}}
    result = transform_pokemon(raw)
    assert result["sprite_url"] == "https://example.com/sprites/1.png"


def test_transform_handles_missing_stat() -> None:
    raw = {**RAW_BULBASAUR, "stats": RAW_BULBASAUR["stats"][:-1]}  # drop speed
    result = transform_pokemon(raw)
    assert result["speed"] is None


def test_transform_extracts_species_id_from_url() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert result["species_id"] == 1


def test_transform_extracts_species_id_for_alternate_form() -> None:
    # e.g. Rotom-Wash (pokemon id 10008) still points back at species 479
    raw = {
        **RAW_BULBASAUR,
        "id": 10008,
        "name": "rotom-wash",
        "species": {"name": "rotom", "url": "https://pokeapi.co/api/v2/pokemon-species/479/"},
    }
    result = transform_pokemon(raw)
    assert result["species_id"] == 479
    assert result["id"] == 10008


def test_transform_carries_is_default() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert result["is_default"] is True

    raw = {**RAW_BULBASAUR, "is_default": False}
    assert transform_pokemon(raw)["is_default"] is False


RAW_NATIONAL_DEX_ENTRY = {
    "entry_number": 479,
    "pokemon_species": {
        "name": "rotom",
        "url": "https://pokeapi.co/api/v2/pokemon-species/479/",
    },
}


def test_transform_species_entry_extracts_id_name_and_dex_number() -> None:
    result = transform_species_entry(RAW_NATIONAL_DEX_ENTRY)
    assert result == {"id": 479, "name": "rotom", "national_dex_number": 479}


def test_transform_species_entry_handles_missing_species_key() -> None:
    result = transform_species_entry({"entry_number": 1})
    assert result == {"id": None, "name": None, "national_dex_number": 1}


def test_transform_species_entry_handles_missing_url() -> None:
    raw = {"entry_number": 1, "pokemon_species": {"name": "bulbasaur"}}
    result = transform_species_entry(raw)
    assert result["id"] is None
    assert result["name"] == "bulbasaur"


def test_transform_species_entry_handles_malformed_url() -> None:
    raw = {
        "entry_number": 1,
        "pokemon_species": {"name": "bulbasaur", "url": "not-a-valid-url"},
    }
    result = transform_species_entry(raw)
    assert result["id"] is None


def test_transform_species_entry_handles_empty_dict() -> None:
    result = transform_species_entry({})
    assert result == {"id": None, "name": None, "national_dex_number": None}


def test_transform_extracts_movepool_move_ids() -> None:
    result = transform_pokemon(RAW_BULBASAUR)
    assert sorted(result["_movepool_move_ids"]) == [33, 45]


def test_transform_handles_missing_moves_key() -> None:
    raw = {k: v for k, v in RAW_BULBASAUR.items() if k != "moves"}
    result = transform_pokemon(raw)
    assert result["_movepool_move_ids"] == []


def test_transform_handles_malformed_move_url() -> None:
    raw = {**RAW_BULBASAUR, "moves": [{"move": {"name": "x", "url": "not-a-valid-url"}}]}
    result = transform_pokemon(raw)
    assert result["_movepool_move_ids"] == []


RAW_TACKLE = {
    "id": 33,
    "name": "tackle",
    "type": {"name": "normal"},
    "damage_class": {"name": "physical"},
    "power": 40,
    "accuracy": 100,
    "pp": 35,
    "priority": 0,
    "effect_chance": None,
}


def test_transform_move_extracts_fields() -> None:
    result = transform_move(RAW_TACKLE)
    assert result == {
        "id": 33,
        "name": "tackle",
        "type": "normal",
        "damage_class": "physical",
        "power": 40,
        "accuracy": 100,
        "pp": 35,
        "priority": 0,
        "effect_chance": None,
        "effect_text": None,
    }


def test_transform_move_handles_missing_type_and_damage_class() -> None:
    raw = {**RAW_TACKLE, "type": None, "damage_class": None}
    result = transform_move(raw)
    assert result["type"] is None
    assert result["damage_class"] is None


def test_transform_move_extracts_english_effect_text() -> None:
    raw = {
        **RAW_TACKLE,
        "effect_entries": [
            {"language": {"name": "de"}, "short_effect": "Nicht Englisch"},
            {"language": {"name": "en"}, "short_effect": "A physical attack."},
        ],
    }
    result = transform_move(raw)
    assert result["effect_text"] == "A physical attack."


def test_transform_move_interpolates_effect_chance() -> None:
    raw = {
        **RAW_TACKLE,
        "effect_chance": 30,
        "effect_entries": [
            {
                "language": {"name": "en"},
                "short_effect": "Has a $effect_chance% chance to burn the target.",
            }
        ],
    }
    result = transform_move(raw)
    assert result["effect_text"] == "Has a 30% chance to burn the target."


def test_transform_move_handles_missing_effect_entries() -> None:
    result = transform_move(RAW_TACKLE)
    assert result["effect_text"] is None


RAW_FIRE_TYPE = {
    "name": "fire",
    "damage_relations": {
        "double_damage_to": [{"name": "ice"}, {"name": "grass"}],
        "half_damage_to": [{"name": "water"}, {"name": "fire"}],
        "no_damage_to": [],
    },
}


def test_transform_type_matchups_covers_every_known_type() -> None:
    all_types = {"fire", "ice", "grass", "water", "normal"}
    rows = transform_type_matchups(RAW_FIRE_TYPE, all_types)
    assert len(rows) == len(all_types)
    by_defender = {r["defending_type"]: r["multiplier"] for r in rows}
    assert by_defender == {
        "ice": 2.0,
        "grass": 2.0,
        "water": 0.5,
        "fire": 0.5,
        "normal": 1.0,  # not listed in any bucket -> implied neutral
    }


def test_transform_type_matchups_sets_attacking_type() -> None:
    rows = transform_type_matchups(RAW_FIRE_TYPE, {"ice"})
    assert rows[0]["attacking_type"] == "fire"


def test_transform_type_matchups_handles_no_damage_to() -> None:
    raw = {"name": "normal", "damage_relations": {"no_damage_to": [{"name": "ghost"}]}}
    rows = transform_type_matchups(raw, {"ghost"})
    assert rows[0]["multiplier"] == 0.0
