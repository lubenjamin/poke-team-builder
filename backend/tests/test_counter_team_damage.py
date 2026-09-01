from app.services.counter_team import estimate_damage, has_stab, resolve_damage_stats


def test_resolve_damage_stats_physical() -> None:
    assert resolve_damage_stats("physical") == ("attack", "defense")


def test_resolve_damage_stats_special() -> None:
    assert resolve_damage_stats("special") == ("special_attack", "special_defense")


def test_resolve_damage_stats_status_deals_no_damage() -> None:
    assert resolve_damage_stats("status") is None


def test_has_stab_true_when_move_type_matches_attacker() -> None:
    assert has_stab("fire", ["fire", "flying"]) is True


def test_has_stab_false_when_move_type_does_not_match() -> None:
    assert has_stab("water", ["fire", "flying"]) is False


def test_estimate_damage_status_move_is_zero() -> None:
    # No power (a status move) -> no direct damage, regardless of stats.
    assert estimate_damage(attacker_stat=150, defender_stat=50, move_power=None, stab=True, type_multiplier=2.0) == 0.0


def test_estimate_damage_immune_defender_is_zero() -> None:
    # 0x type multiplier (immune) -> no damage even with a strong attacker/move.
    assert estimate_damage(attacker_stat=150, defender_stat=50, move_power=90, stab=True, type_multiplier=0.0) == 0.0


def test_estimate_damage_stab_increases_damage() -> None:
    no_stab = estimate_damage(attacker_stat=100, defender_stat=100, move_power=80, stab=False, type_multiplier=1.0)
    with_stab = estimate_damage(attacker_stat=100, defender_stat=100, move_power=80, stab=True, type_multiplier=1.0)
    assert with_stab == no_stab * 1.5


def test_estimate_damage_super_effective_increases_damage() -> None:
    neutral = estimate_damage(attacker_stat=100, defender_stat=100, move_power=80, stab=False, type_multiplier=1.0)
    super_effective = estimate_damage(attacker_stat=100, defender_stat=100, move_power=80, stab=False, type_multiplier=2.0)
    assert super_effective == neutral * 2.0


def test_estimate_damage_higher_attacker_stat_increases_damage() -> None:
    weaker = estimate_damage(attacker_stat=80, defender_stat=100, move_power=80, stab=False, type_multiplier=1.0)
    stronger = estimate_damage(attacker_stat=160, defender_stat=100, move_power=80, stab=False, type_multiplier=1.0)
    assert stronger > weaker


def test_estimate_damage_higher_defender_stat_decreases_damage() -> None:
    weaker_defense = estimate_damage(attacker_stat=100, defender_stat=80, move_power=80, stab=False, type_multiplier=1.0)
    stronger_defense = estimate_damage(attacker_stat=100, defender_stat=160, move_power=80, stab=False, type_multiplier=1.0)
    assert stronger_defense < weaker_defense


def test_estimate_damage_zero_defender_stat_does_not_crash() -> None:
    # No real Pokemon has a 0 stat, but guard against a divide-by-zero anyway.
    result = estimate_damage(attacker_stat=100, defender_stat=0, move_power=80, stab=False, type_multiplier=1.0)
    assert result > 0
