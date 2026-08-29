from app.services.ingestion import transform_pokemon, transform_species_entry

RAW_BULBASAUR = {
    "id": 1,
    "name": "bulbasaur",
    "is_default": True,
    "species": {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
    "types": [
        {"slot": 2, "type": {"name": "poison", "url": "..."}},
        {"slot": 1, "type": {"name": "grass", "url": "..."}},
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
