import pytest

from app.models import Move, Pokemon
from app.services.counter_team import (
    BattleRosterSlot,
    _best_move_against,
    _combined_type_multiplier,
    score_candidate,
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
        damage_class="physical",
        power=80,
        accuracy=100,
        pp=15,
        priority=0,
        effect_chance=None,
        effect_text=None,
    )
    defaults.update(overrides)
    return Move(**defaults)


TYPE_MATRIX = {
    "fire": {"grass": 2.0, "poison": 1.0},
    "grass": {"fire": 0.5, "flying": 0.5, "poison": 1.0},
}


def test_combined_type_multiplier_multiplies_across_dual_types() -> None:
    # Grass vs a Fire/Flying defender: 0.5 (vs fire) * 0.5 (vs flying) = 0.25
    assert _combined_type_multiplier(TYPE_MATRIX, "grass", ["fire", "flying"]) == 0.25


def test_combined_type_multiplier_defaults_unknown_pair_to_neutral() -> None:
    assert _combined_type_multiplier(TYPE_MATRIX, "fire", ["dragon"]) == 1.0


def test_best_move_against_skips_status_moves() -> None:
    attacker = _make_pokemon(types=["fire"])
    defender = _make_pokemon(types=["grass"])
    status_move = _make_move(name="growl", damage_class="status", power=None)
    attack_move = _make_move(name="ember", type="fire", damage_class="special", power=40)

    result = _best_move_against(attacker, [status_move, attack_move], defender, TYPE_MATRIX)

    assert result.move is attack_move
    assert result.damage_pct > 0


def test_best_move_against_picks_highest_damage_not_first_listed() -> None:
    attacker = _make_pokemon(types=["fire"], special_attack=100)
    defender = _make_pokemon(types=["grass"], special_defense=100, hp=100)
    weak_move = _make_move(name="ember", type="fire", damage_class="special", power=40)
    strong_move = _make_move(name="fire-blast", type="fire", damage_class="special", power=110)

    result = _best_move_against(attacker, [weak_move, strong_move], defender, TYPE_MATRIX)

    assert result.move is strong_move


def test_score_candidate_favorable_matchup_hand_computed() -> None:
    # Charizard-like vs Venusaur-like: candidate's Flamethrower is
    # super-effective + STAB, opponent's Vine Whip is quadruple-resisted
    # (grass vs fire/flying = 0.5 * 0.5), and the candidate is faster.
    candidate = _make_pokemon(
        id=6, name="charizard", types=["fire", "flying"],
        hp=100, special_attack=109, defense=78, speed=100,
    )
    flamethrower = _make_move(name="flamethrower", type="fire", damage_class="special", power=90)

    opponent = _make_pokemon(
        id=3, name="venusaur", types=["grass", "poison"],
        hp=100, attack=80, special_defense=100, speed=80,
    )
    vine_whip = _make_move(name="vine-whip", type="grass", damage_class="physical", power=45)

    result = score_candidate(
        candidate=candidate,
        candidate_movepool=[flamethrower],
        opponent_roster=[BattleRosterSlot(pokemon=opponent, moves=[vine_whip])],
        type_matrix=TYPE_MATRIX,
    )

    assert result.offensive_threat == pytest.approx(1.3549, abs=0.001)
    assert result.vulnerability == pytest.approx(0.0837, abs=0.001)
    assert result.speed_edge == 1.0  # candidate is faster, same priority
    assert result.fitness == pytest.approx(1.7712, abs=0.001)
    assert result.offensive_threat > result.vulnerability


def test_score_candidate_unfavorable_matchup_has_lower_fitness() -> None:
    # Same pair, but roles reversed: candidate is now the one who's
    # quadruple-resisted and slower, opponent hits it super-effectively.
    weak_candidate = _make_pokemon(
        id=3, name="venusaur", types=["grass", "poison"],
        hp=100, attack=80, defense=78, speed=80,
    )
    vine_whip = _make_move(name="vine-whip", type="grass", damage_class="physical", power=45)

    strong_opponent = _make_pokemon(
        id=6, name="charizard", types=["fire", "flying"],
        hp=100, special_attack=109, special_defense=100, speed=100,
    )
    flamethrower = _make_move(name="flamethrower", type="fire", damage_class="special", power=90)

    result = score_candidate(
        candidate=weak_candidate,
        candidate_movepool=[vine_whip],
        opponent_roster=[BattleRosterSlot(pokemon=strong_opponent, moves=[flamethrower])],
        type_matrix=TYPE_MATRIX,
    )

    assert result.fitness < 0
    assert result.speed_edge == 0.0  # candidate is slower here


def test_score_candidate_averages_across_multiple_opponents() -> None:
    candidate = _make_pokemon(types=["fire"], special_attack=100, speed=100)
    move = _make_move(type="fire", damage_class="special", power=80)

    easy_target = _make_pokemon(id=1, types=["grass"], special_defense=100, hp=100, speed=50)
    hard_target = _make_pokemon(id=2, types=["fire"], special_defense=100, hp=100, speed=50)
    filler_move = _make_move(type="normal", damage_class="physical", power=40)

    result = score_candidate(
        candidate=candidate,
        candidate_movepool=[move],
        opponent_roster=[
            BattleRosterSlot(pokemon=easy_target, moves=[filler_move]),
            BattleRosterSlot(pokemon=hard_target, moves=[filler_move]),
        ],
        type_matrix=TYPE_MATRIX,
    )

    # Fire vs grass (2.0x) and fire vs fire (0.5x, not in TYPE_MATRIX so
    # defaults to neutral 1.0x here) average to something between the two
    # single-opponent cases, not equal to either.
    single_easy = score_candidate(
        candidate, [move], [BattleRosterSlot(pokemon=easy_target, moves=[filler_move])], TYPE_MATRIX
    )
    assert result.offensive_threat < single_easy.offensive_threat


def test_score_candidate_with_no_damaging_moves_has_zero_offense() -> None:
    candidate = _make_pokemon()
    status_only = [_make_move(damage_class="status", power=None)]
    opponent = _make_pokemon()

    result = score_candidate(
        candidate=candidate,
        candidate_movepool=status_only,
        opponent_roster=[BattleRosterSlot(pokemon=opponent, moves=status_only)],
        type_matrix=TYPE_MATRIX,
    )

    assert result.offensive_threat == 0.0
    assert result.vulnerability == 0.0
