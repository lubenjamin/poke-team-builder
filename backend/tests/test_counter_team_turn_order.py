from app.services.counter_team import acts_first


def test_higher_priority_wins_regardless_of_speed() -> None:
    # Priority 1 move (e.g. Quick Attack) beats priority 0, even if the
    # attacker is much slower.
    assert acts_first(attacker_priority=1, attacker_speed=10, defender_priority=0, defender_speed=200) is True


def test_lower_priority_loses_regardless_of_speed() -> None:
    assert acts_first(attacker_priority=0, attacker_speed=200, defender_priority=1, defender_speed=10) is False


def test_equal_priority_faster_speed_wins() -> None:
    assert acts_first(attacker_priority=0, attacker_speed=150, defender_priority=0, defender_speed=100) is True


def test_equal_priority_slower_speed_loses() -> None:
    assert acts_first(attacker_priority=0, attacker_speed=100, defender_priority=0, defender_speed=150) is False


def test_exact_tie_conservatively_does_not_credit_attacker() -> None:
    # Equal priority AND equal speed is a random 50/50 in the real games;
    # this deterministic generator scores it as the attacker NOT going
    # first rather than guessing.
    assert acts_first(attacker_priority=0, attacker_speed=100, defender_priority=0, defender_speed=100) is False


def test_negative_priority_move_still_compares_correctly() -> None:
    # e.g. Trick Room (priority -7) vs a normal-priority move.
    assert acts_first(attacker_priority=-7, attacker_speed=200, defender_priority=0, defender_speed=1) is False
