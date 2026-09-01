from app.models import Move, Pokemon
from app.services.counter_team import (
    BattleRosterSlot,
    _movepool_damage_table,
    select_moves_for_coverage,
)


def _make_pokemon(**overrides: object) -> Pokemon:
    defaults = dict(
        id=1,
        name="test-mon",
        species_id=1,
        is_default=True,
        sprite_url="https://example.com/sprite.png",
        types=["normal"],
        hp=100,
        attack=100,
        defense=100,
        special_attack=100,
        special_defense=100,
        speed=100,
    )
    defaults.update(overrides)
    return Pokemon(**defaults)


def _make_move(**overrides: object) -> Move:
    defaults = dict(
        id=1,
        name="test-move",
        type="normal",
        damage_class="special",
        power=90,
        accuracy=100,
        pp=15,
        priority=0,
        effect_chance=None,
        effect_text=None,
    )
    defaults.update(overrides)
    return Move(**defaults)


# A synthetic type chart, deliberately simple: fire beats grass, is weak to
# water; ground beats electric; everything else is neutral (1.0). Chosen so
# expected damage-% values are hand-computable, not to mirror real Pokemon
# type matchups.
TYPE_MATRIX = {
    "fire": {"grass": 2.0, "water": 0.5, "electric": 1.0},
    "water": {"grass": 0.5, "water": 1.0, "electric": 1.0},
    "ground": {"grass": 1.0, "water": 1.0, "electric": 2.0},
    "normal": {"grass": 1.0, "water": 1.0, "electric": 1.0},
}


def test_select_moves_for_coverage_excludes_status_moves() -> None:
    attacker = _make_pokemon()
    status_move = _make_move(damage_class="status", power=None)
    opponents = [BattleRosterSlot(pokemon=_make_pokemon(), moves=[])]

    table = _movepool_damage_table(attacker, [status_move], opponents, TYPE_MATRIX)
    result = select_moves_for_coverage([status_move], opponents, table)

    assert result == []


def test_select_moves_for_coverage_hand_computed_greedy_order_then_pads() -> None:
    # Attacker with no STAB on any of its moves (types=["normal"]), three
    # single-type opponents (grass/water/electric), and three damaging
    # moves whose coverage deliberately overlaps: ground_move alone already
    # covers electric (2x) and ties water/grass at neutral (1x); fire_move
    # adds a genuinely new best answer for grass (2x, beating ground's 1x
    # there); water_move never becomes anyone's best answer once those two
    # are picked, so the coverage loop itself stops after 2 picks — but
    # water_move still gets appended as a padding pick so the moveset isn't
    # left at 2 when max_moves=4 allows more.
    attacker = _make_pokemon(types=["normal"])
    grass_opp = _make_pokemon(id=10, types=["grass"])
    water_opp = _make_pokemon(id=20, types=["water"])
    electric_opp = _make_pokemon(id=30, types=["electric"])

    fire_move = _make_move(id=1, name="fire-move", type="fire")
    water_move = _make_move(id=2, name="water-move", type="water")
    ground_move = _make_move(id=3, name="ground-move", type="ground")

    movepool = [fire_move, water_move, ground_move]
    opponents = [
        BattleRosterSlot(pokemon=grass_opp, moves=[]),
        BattleRosterSlot(pokemon=water_opp, moves=[]),
        BattleRosterSlot(pokemon=electric_opp, moves=[]),
    ]

    table = _movepool_damage_table(attacker, movepool, opponents, TYPE_MATRIX)
    result = select_moves_for_coverage(movepool, opponents, table, max_moves=4)

    # ground_move has the highest total single-move coverage (2x vs
    # electric + neutral elsewhere) and goes first via real marginal-gain
    # competition; fire_move is the only remaining move that raises the
    # team's best answer against any opponent (grass, 2x beats ground's
    # neutral there) and goes second, also via marginal gain. water_move
    # never exceeds what's already covered by either pick, so the coverage
    # loop stops there — but it's still the only move left, so it's
    # appended as a padding pick, landing third.
    assert [m.name for m in result] == ["ground-move", "fire-move", "water-move"]


def test_select_moves_for_coverage_pads_by_peak_damage_when_coverage_plateaus() -> None:
    # A single opponent and three same-target moves that only differ in
    # power (no type multiplier or STAB differences, so damage is strictly
    # monotonic in power). Only the highest-power move ever has positive
    # marginal gain -- the other two are strictly weaker against the one
    # opponent that exists, so they can never beat what's already covered.
    # Padding should still fill the remaining slots, ordered by each move's
    # own best single-target damage (highest power first).
    attacker = _make_pokemon(types=["normal"])
    opponent = _make_pokemon(id=99, types=["grass"])
    strong = _make_move(id=1, name="strong-move", type="fighting", power=100)
    medium = _make_move(id=2, name="medium-move", type="fighting", power=80)
    weak = _make_move(id=3, name="weak-move", type="fighting", power=60)

    movepool = [medium, weak, strong]  # deliberately not pre-sorted
    opponents = [BattleRosterSlot(pokemon=opponent, moves=[])]

    table = _movepool_damage_table(attacker, movepool, opponents, TYPE_MATRIX)
    result = select_moves_for_coverage(movepool, opponents, table, max_moves=4)

    assert [m.name for m in result] == ["strong-move", "medium-move", "weak-move"]


def test_select_moves_for_coverage_respects_max_moves_cap() -> None:
    # Four moves, each uniquely super-effective against one of four
    # opponents and neutral against the rest — every move keeps
    # contributing positive marginal coverage even after two are picked,
    # so without a cap greedy would keep going. max_moves=2 should stop it
    # at exactly 2 regardless.
    symmetric_matrix = {
        "a": {"a": 2.0, "b": 1.0, "c": 1.0, "d": 1.0},
        "b": {"a": 1.0, "b": 2.0, "c": 1.0, "d": 1.0},
        "c": {"a": 1.0, "b": 1.0, "c": 2.0, "d": 1.0},
        "d": {"a": 1.0, "b": 1.0, "c": 1.0, "d": 2.0},
    }
    attacker = _make_pokemon(types=["normal"])
    opponents = [
        BattleRosterSlot(pokemon=_make_pokemon(id=i, types=[t]), moves=[])
        for i, t in enumerate(["a", "b", "c", "d"], start=1)
    ]
    movepool = [_make_move(id=i, name=f"move-{t}", type=t) for i, t in enumerate(["a", "b", "c", "d"], start=1)]

    table = _movepool_damage_table(attacker, movepool, opponents, symmetric_matrix)
    result = select_moves_for_coverage(movepool, opponents, table, max_moves=2)

    assert len(result) == 2


def test_select_moves_for_coverage_empty_movepool_returns_empty() -> None:
    attacker = _make_pokemon()
    opponents = [BattleRosterSlot(pokemon=_make_pokemon(), moves=[])]

    table = _movepool_damage_table(attacker, [], opponents, TYPE_MATRIX)
    result = select_moves_for_coverage([], opponents, table)

    assert result == []
