from app.models import Move, Pokemon
from app.services.change_detection import (
    _TRACKED_FIELDS,
    _TRACKED_MOVE_FIELDS,
    _snapshot,
    _stringify,
)


def _make_pokemon(**overrides: object) -> Pokemon:
    defaults = dict(
        id=25,
        name="pikachu",
        species_id=25,
        is_default=True,
        sprite_url="https://example.com/pikachu.png",
        types=["electric"],
        hp=35,
        attack=55,
        defense=40,
        special_attack=50,
        special_defense=50,
        speed=90,
    )
    defaults.update(overrides)
    return Pokemon(**defaults)


def _make_move(**overrides: object) -> Move:
    defaults = dict(
        id=94,
        name="psychic",
        type="psychic",
        damage_class="special",
        power=90,
        accuracy=100,
        pp=10,
        priority=0,
        effect_chance=10,
        effect_text="10% chance to lower the target's Sp. Def by 1 stage.",
    )
    defaults.update(overrides)
    return Move(**defaults)


def test_stringify_joins_lists_but_leaves_scalars_alone() -> None:
    assert _stringify(["electric", "flying"]) == "electric, flying"
    assert _stringify(35) == "35"
    assert _stringify("pikachu") == "pikachu"


def test_snapshot_only_covers_tracked_fields() -> None:
    pokemon = _make_pokemon()
    snapshot = _snapshot(pokemon, _TRACKED_FIELDS)
    assert set(snapshot) == set(_TRACKED_FIELDS)
    assert "species_id" not in snapshot  # internal bookkeeping, not user-visible
    assert "is_default" not in snapshot
    assert snapshot["types"] == "electric"
    assert snapshot["hp"] == "35"


def test_snapshot_detects_a_changed_pokemon_field() -> None:
    before = _snapshot(_make_pokemon(hp=35), _TRACKED_FIELDS)
    after = _snapshot(_make_pokemon(hp=40), _TRACKED_FIELDS)
    changed = [f for f in _TRACKED_FIELDS if before[f] != after[f]]
    assert changed == ["hp"]


def test_snapshot_sees_no_change_for_identical_pokemon() -> None:
    before = _snapshot(_make_pokemon(), _TRACKED_FIELDS)
    after = _snapshot(_make_pokemon(), _TRACKED_FIELDS)
    changed = [f for f in _TRACKED_FIELDS if before[f] != after[f]]
    assert changed == []


def test_snapshot_only_covers_tracked_move_fields() -> None:
    move = _make_move()
    snapshot = _snapshot(move, _TRACKED_MOVE_FIELDS)
    assert set(snapshot) == set(_TRACKED_MOVE_FIELDS)
    assert "id" not in snapshot
    assert snapshot["power"] == "90"


def test_snapshot_detects_a_changed_move_field() -> None:
    before = _snapshot(_make_move(power=90), _TRACKED_MOVE_FIELDS)
    after = _snapshot(_make_move(power=100), _TRACKED_MOVE_FIELDS)
    changed = [f for f in _TRACKED_MOVE_FIELDS if before[f] != after[f]]
    assert changed == ["power"]


def test_snapshot_sees_no_change_for_identical_move() -> None:
    before = _snapshot(_make_move(), _TRACKED_MOVE_FIELDS)
    after = _snapshot(_make_move(), _TRACKED_MOVE_FIELDS)
    changed = [f for f in _TRACKED_MOVE_FIELDS if before[f] != after[f]]
    assert changed == []
