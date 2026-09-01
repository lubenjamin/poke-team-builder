from app.models import Pokemon
from app.services.counter_team import CandidateScore, select_counter_team


def _score(species_id: int, types: list[str], fitness: float) -> CandidateScore:
    pokemon = Pokemon(id=species_id, name=f"mon-{species_id}", species_id=species_id, types=types)
    return CandidateScore(
        pokemon=pokemon,
        offensive_threat=0.0,
        vulnerability=0.0,
        speed_edge=0.0,
        fitness=fitness,
        movepool_damage_table={},
    )


def test_select_counter_team_respects_team_size() -> None:
    candidates = [_score(i, ["normal"], fitness=float(i)) for i in range(10)]
    team = select_counter_team(candidates, team_size=6)
    assert len(team) == 6


def test_select_counter_team_returns_fewer_if_not_enough_distinct_species() -> None:
    candidates = [_score(1, ["fire"], 3.0), _score(2, ["water"], 2.0), _score(3, ["grass"], 1.0)]
    team = select_counter_team(candidates, team_size=6)
    assert len(team) == 3


def test_select_counter_team_never_repeats_a_species() -> None:
    # Two "forms" of the same species (e.g. Rotom / Rotom-Wash) — only one
    # should ever make the team, same rule as saved rosters.
    same_species = [
        _score(479, ["electric", "ghost"], 5.0),
        _score(479, ["electric", "water"], 4.0),  # same species_id, higher fitness doesn't matter after the first pick
    ]
    other = [_score(6, ["fire", "flying"], 3.0)]
    team = select_counter_team(same_species + other, team_size=6)
    picked_species = [c.pokemon.species_id for c in team]
    assert picked_species.count(479) == 1
    assert len(team) == 2


def test_select_counter_team_picks_highest_fitness_when_no_type_overlap() -> None:
    candidates = [
        _score(1, ["fire"], 3.0),
        _score(2, ["water"], 2.0),
        _score(3, ["grass"], 1.0),
    ]
    team = select_counter_team(candidates, team_size=3)
    assert [c.pokemon.species_id for c in team] == [1, 2, 3]


def test_select_counter_team_penalizes_repeated_single_type_overlap() -> None:
    # A (fire, fitness 2.0) goes first. Remaining: B (water, 1.9, no
    # overlap) vs C (fire, 1.95, one shared type with A). Raw fitness
    # favors C, but the 0.15 overlap penalty flips it: adjusted C =
    # 1.95 - 0.15*1 = 1.80 < adjusted B = 1.9 - 0 = 1.9.
    candidates = [
        _score(1, ["fire"], 2.0),
        _score(2, ["water"], 1.9),
        _score(3, ["fire"], 1.95),
    ]
    team = select_counter_team(candidates, team_size=2)
    assert [c.pokemon.species_id for c in team] == [1, 2]


def test_select_counter_team_dual_type_overlap_penalized_twice_as_much() -> None:
    # A (fire/flying) goes first. D fully overlaps both of A's types
    # (penalty = 0.15*2 = 0.30); E overlaps only one (penalty = 0.15*1 =
    # 0.15). Fitness gap (0.1) is smaller than the penalty gap (0.15), so
    # the single-type-overlap candidate should win the second slot.
    candidates = [
        _score(1, ["fire", "flying"], 3.0),
        _score(2, ["fire", "flying"], 2.5),  # D: full overlap
        _score(3, ["fire", "water"], 2.4),  # E: partial overlap
    ]
    team = select_counter_team(candidates, team_size=2)
    assert [c.pokemon.species_id for c in team] == [1, 3]

    # Confirm the exact adjusted scores behind that outcome.
    d_adjusted = 2.5 - 0.15 * 2
    e_adjusted = 2.4 - 0.15 * 1
    assert e_adjusted > d_adjusted
