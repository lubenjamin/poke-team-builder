from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Move, Pokemon, PokemonMovepool
from app.schemas.pokemon import MoveRead, PokemonRead
from app.schemas.team import TeamPokemonRead
from app.services.type_effectiveness import fetch_full_type_matrix

MAX_MOVES_PER_POKEMON = 4
BATTLE_LEVEL = 50  # standard competitive convention (VGC-style rules)
STAB_MULTIPLIER = 1.5  # same-type-attack-bonus


def resolve_damage_stats(damage_class: str) -> tuple[str, str] | None:
    """Which Pokemon stat fields a move's damage class uses for the damage
    formula: physical uses Attack/Defense, special uses Sp.Atk/Sp.Def.
    Status moves deal no direct damage — returns None so the caller can
    skip them rather than mistakenly running a damage calc on one."""
    if damage_class == "physical":
        return ("attack", "defense")
    if damage_class == "special":
        return ("special_attack", "special_defense")
    return None


def has_stab(move_type: str, attacker_types: list[str]) -> bool:
    """Same-Type Attack Bonus: does the move's type match one of the
    attacker's own types?"""
    return move_type in attacker_types


def estimate_damage(
    attacker_stat: int,
    defender_stat: int,
    move_power: int | None,
    stab: bool,
    type_multiplier: float,
) -> float:
    """Simplified Gen 3+ damage formula, level fixed at BATTLE_LEVEL — a
    relative scoring signal for ranking candidates/moves against each
    other, not a battle-accurate calculator:  data model has no
    EVs/IVs/natures/abilities, so `attacker_stat`/`defender_stat` are base stats, 
    not real battle stats. Deliberately omits the random 0.85-1.0 roll, critical hits, weather,
    and status effects (e.g. burn halving physical damage).

    Returns 0.0 for a non-damaging move (no power, e.g. a status move) or
    when `type_multiplier` is 0 (the defender is immune) — both are
    legitimate "this move does nothing" results, not errors."""
    if not move_power or move_power <= 0 or type_multiplier <= 0:
        return 0.0

    defender_stat = max(defender_stat, 1)  # guard a stray 0 — no real Pokemon has one
    base = (2 * BATTLE_LEVEL / 5 + 2) * move_power * attacker_stat / defender_stat / 50 + 2
    stab_multiplier = STAB_MULTIPLIER if stab else 1.0
    return base * stab_multiplier * type_multiplier


def acts_first(
    attacker_priority: int,
    attacker_speed: int,
    defender_priority: int,
    defender_speed: int,
) -> bool:
    """True if the attacker's move goes before the defender's, per standard
    turn-order rules: higher move priority always wins regardless of speed;
    a priority tie is broken by higher Speed. A true tie in both priority
    and speed is a random 50/50 in the real games — since this generator is
    deterministic (no dice rolls anywhere in it), an exact tie is
    conservatively scored as the attacker NOT going first, rather than
    crediting an uncertain outcome as a guaranteed advantage."""
    if attacker_priority != defender_priority:
        return attacker_priority > defender_priority
    return attacker_speed > defender_speed


def _combined_type_multiplier(
    type_matrix: dict[str, dict[str, float]], attacking_type: str, defending_types: list[str]
) -> float:
    """One attacking type's combined multiplier against a (possibly
    dual-typed) defender — multiply across the defender's 1-2 types, same
    logic as compute_type_effectiveness and the frontend's
    TeamDefenseMatrix, just for one attacking type at a time against an
    already-fetched full chart (no DB query) rather than the other
    direction (all attacking types against a fixed defender)."""
    result = 1.0
    for defending_type in defending_types:
        result *= type_matrix.get(attacking_type, {}).get(defending_type, 1.0)
    return result


@dataclass
class BattleRosterSlot:
    """One Pokemon + the moves it actually has equipped — used both for the
    opponent roster (fixed, submitted by the user) and, once picked, our
    own generated team."""

    pokemon: Pokemon
    moves: list[Move]


@dataclass
class BestMoveResult:
    move: Move | None
    damage_pct: float  # estimated damage as a fraction of the defender's HP stat


def _best_move_against(
    attacker: Pokemon,
    attacker_moves: list[Move],
    defender: Pokemon,
    type_matrix: dict[str, dict[str, float]],
) -> BestMoveResult:
    """The single highest-damage move among attacker_moves against
    defender, damage expressed as a % of the defender's HP (not a raw
    magnitude — raw damage isn't comparable across Pokemon with very
    different HP pools). Used in both directions by score_candidate: a
    candidate's best move against an opponent (offensive threat), and an
    opponent's best *actual equipped* move against a candidate
    (vulnerability) — same function, attacker/defender swapped."""
    best_move: Move | None = None
    best_damage_pct = 0.0
    for move in attacker_moves:
        stat_names = resolve_damage_stats(move.damage_class)
        if stat_names is None:
            continue  # status move — deals no direct damage
        attacker_stat = getattr(attacker, stat_names[0])
        defender_stat = getattr(defender, stat_names[1])
        type_multiplier = _combined_type_multiplier(type_matrix, move.type, defender.types)
        damage = estimate_damage(
            attacker_stat,
            defender_stat,
            move.power,
            has_stab(move.type, attacker.types),
            type_multiplier,
        )
        damage_pct = damage / max(defender.hp, 1)
        if damage_pct > best_damage_pct:
            best_damage_pct = damage_pct
            best_move = move
    return BestMoveResult(move=best_move, damage_pct=best_damage_pct)


def _movepool_damage_table(
    attacker: Pokemon,
    movepool: list[Move],
    opponent_roster: list[BattleRosterSlot],
    type_matrix: dict[str, dict[str, float]],
) -> dict[int, dict[int, float]]:
    """move.id -> {opponent.pokemon.id: damage_pct} for every damaging move
    in movepool against every opponent in opponent_roster. Status moves
    are excluded outright (resolve_damage_stats returns None for them).

    This is the one place estimate_damage actually gets called for a
    candidate's own movepool. score_candidate only ever needs the
    per-opponent max out of it (via _best_move_from_table below), and
    select_moves_for_coverage needs every cell to run greedy coverage
    selection — both consume the exact same movepool x opponent grid, so
    it gets computed once per candidate and shared, rather than once for
    scoring and again for move selection."""
    table: dict[int, dict[int, float]] = {}
    for move in movepool:
        stat_names = resolve_damage_stats(move.damage_class)
        if stat_names is None:
            continue  # status move — no direct damage to tabulate
        attacker_stat = getattr(attacker, stat_names[0])
        row: dict[int, float] = {}
        for opponent_slot in opponent_roster:
            opponent = opponent_slot.pokemon
            defender_stat = getattr(opponent, stat_names[1])
            type_multiplier = _combined_type_multiplier(type_matrix, move.type, opponent.types)
            damage = estimate_damage(
                attacker_stat,
                defender_stat,
                move.power,
                has_stab(move.type, attacker.types),
                type_multiplier,
            )
            row[opponent.id] = damage / max(opponent.hp, 1)
        table[move.id] = row
    return table


def _best_move_from_table(
    movepool: list[Move],
    damage_table: dict[int, dict[int, float]],
    opponent_id: int,
) -> BestMoveResult:
    """Same result shape as _best_move_against, but reads damage-% values
    out of an already-built _movepool_damage_table instead of recomputing
    the damage formula — the offense side of score_candidate uses this
    once it has a table for the candidate's full movepool."""
    best_move: Move | None = None
    best_damage_pct = 0.0
    for move in movepool:
        row = damage_table.get(move.id)
        if row is None:
            continue  # status move — excluded from the table
        damage_pct = row.get(opponent_id, 0.0)
        if damage_pct > best_damage_pct:
            best_damage_pct = damage_pct
            best_move = move
    return BestMoveResult(move=best_move, damage_pct=best_damage_pct)


@dataclass
class CandidateScore:
    """Stage A output for one candidate Pokemon, scored against the fixed
    opponent roster — ranks/filters candidates (Stage B) independent of
    which other candidates end up on the final team."""

    pokemon: Pokemon
    offensive_threat: float
    vulnerability: float
    speed_edge: float
    fitness: float
    movepool_damage_table: dict[int, dict[int, float]]
    """move.id -> {opponent.pokemon.id: damage_pct}, the same table
    _movepool_damage_table built while computing offensive_threat — carried
    forward so Stage C (select_moves_for_coverage) can reuse it for
    whichever candidates Stage B actually picks, instead of rebuilding it."""


SPEED_EDGE_WEIGHT = 0.5


def score_candidate(
    candidate: Pokemon,
    candidate_movepool: list[Move],
    opponent_roster: list[BattleRosterSlot],
    type_matrix: dict[str, dict[str, float]],
) -> CandidateScore:
    """Stage A: score one legal candidate against the opponent's whole
    roster. Three signals, averaged across all 6 opponents:

    - offensive_threat: the candidate's single best movepool move's damage
      (as % of HP) against each opponent.
    - vulnerability: the WORST hit each opponent's *actual equipped* moves
      can land on the candidate — deliberately their real committed
      moveset, not their whole movepool, since that's the genuine threat
      this candidate would face.
    - speed_edge: the fraction of opponents against whom the candidate's
      best move would go first (acts_first on that move pair's priority
      and both Pokemon's speed).

    fitness = offensive_threat - vulnerability + SPEED_EDGE_WEIGHT * speed_edge
    """
    damage_table = _movepool_damage_table(candidate, candidate_movepool, opponent_roster, type_matrix)

    offensive_hits: list[float] = []
    vulnerability_hits: list[float] = []
    speed_wins = 0

    for opponent_slot in opponent_roster:
        opponent = opponent_slot.pokemon

        offense = _best_move_from_table(candidate_movepool, damage_table, opponent.id)
        defense = _best_move_against(opponent, opponent_slot.moves, candidate, type_matrix)

        offensive_hits.append(offense.damage_pct)
        vulnerability_hits.append(defense.damage_pct)

        if offense.move is not None and defense.move is not None and acts_first(
            offense.move.priority, candidate.speed, defense.move.priority, opponent.speed
        ):
            speed_wins += 1

    opponent_count = len(opponent_roster) or 1
    offensive_threat = sum(offensive_hits) / opponent_count
    vulnerability = sum(vulnerability_hits) / opponent_count
    speed_edge = speed_wins / opponent_count
    fitness = offensive_threat - vulnerability + SPEED_EDGE_WEIGHT * speed_edge

    return CandidateScore(
        pokemon=candidate,
        offensive_threat=offensive_threat,
        vulnerability=vulnerability,
        speed_edge=speed_edge,
        fitness=fitness,
        movepool_damage_table=damage_table,
    )


TYPE_OVERLAP_PENALTY_WEIGHT = 0.15


def select_counter_team(
    candidate_scores: list[CandidateScore], team_size: int
) -> list[CandidateScore]:
    """Stage B: greedily build a team out of Stage A's per-candidate scores.

    Not just "top N by fitness" — that can pick 6 candidates that all beat
    the *same* one or two opponents while doing nothing against the rest,
    and that all share a typing, so a single well-placed coverage move
    threatens the whole team at once. Each round, pick whichever remaining
    candidate maximizes fitness minus a penalty for how much its typing
    overlaps the team already assembled so far (each shared type with an
    already-picked teammate subtracts TYPE_OVERLAP_PENALTY_WEIGHT, so a
    dual-type match against one existing teammate is penalized twice as
    heavily as a single-type match). This is re-scored every round, since
    the penalty depends on who's already on the team.

    Same one-form-per-species rule as saved rosters: a species already
    represented on the team is skipped entirely, not just penalized.

    Runtime: O(team_size * N) comparisons against the candidate pool
    (~1187 legal candidates today), so ~6 * 1187 ~= 7000 comparisons for a
    full team — trivial regardless of catalog size.

    Returns fewer than team_size only if there aren't enough distinct
    species left to fill it (never an error)."""
    remaining = list(candidate_scores)
    chosen: list[CandidateScore] = []
    chosen_species: set[int] = set()
    chosen_types: list[str] = []

    while remaining and len(chosen) < team_size:
        best: CandidateScore | None = None
        best_adjusted = float("-inf")
        for candidate in remaining:
            if candidate.pokemon.species_id in chosen_species:
                continue
            overlap = sum(1 for t in candidate.pokemon.types if t in chosen_types)
            adjusted = candidate.fitness - TYPE_OVERLAP_PENALTY_WEIGHT * overlap
            if adjusted > best_adjusted:
                best_adjusted = adjusted
                best = candidate

        if best is None:
            break  # no remaining candidate has an unrepresented species

        chosen.append(best)
        chosen_species.add(best.pokemon.species_id)
        chosen_types.extend(best.pokemon.types)
        remaining.remove(best)

    return chosen


def select_moves_for_coverage(
    movepool: list[Move],
    opponent_roster: list[BattleRosterSlot],
    damage_table: dict[int, dict[int, float]],
    max_moves: int = MAX_MOVES_PER_POKEMON,
) -> list[Move]:
    """Stage C: pick up to max_moves moves from a chosen teammate's movepool
    that together answer as much of the opponent roster as possible.

    Consumes an already-built _movepool_damage_table (typically the one
    score_candidate already computed for this candidate — see
    CandidateScore.movepool_damage_table) rather than recomputing damage
    itself, since Stage A already had to run the exact same movepool x
    opponent damage calc once to score this candidate in the first place.

    This is the classic greedy weighted-maximum-coverage algorithm: track
    the best damage-% each opponent has taken from any move picked so far
    (starts at 0 for everyone), and repeatedly add whichever remaining move
    raises that running best-per-opponent total the most. A move that
    merely re-hits an opponent the team already answers well contributes
    little marginal gain even if it's individually powerful; a move that
    answers an opponent nothing else covers contributes a lot. Greedy is
    the standard approach here — exact optimal coverage is NP-hard, but
    greedy is provably within ~63% (1 - 1/e) of optimal for this kind of
    problem, and with at most a few dozen movepool entries x up to 4 picks
    it's effectively instant.

    Status moves are absent from damage_table (_movepool_damage_table
    excludes them outright — they contribute no direct-damage coverage).
    The coverage loop itself stops early once no remaining move adds any
    further coverage — but rather than leave the slot empty, whatever's
    left over is padded with each remaining move's best single-target hit
    (highest damage-% against any one opponent), so a teammate doesn't come
    out with a thinner-than-normal moveset. Those padding picks add no
    marginal coverage — that's exactly why the loop above didn't pick them
    — they're just the next-best individual hits, same as a real player's
    4th move slot often being "hits this one specific threat hard" rather
    than something that changes the matchup.
    """
    best_per_opponent: dict[int, float] = {slot.pokemon.id: 0.0 for slot in opponent_roster}
    chosen: list[Move] = []
    remaining = [m for m in movepool if m.id in damage_table]

    while remaining and len(chosen) < max_moves:
        best_move: Move | None = None
        best_gain = 0.0
        for move in remaining:
            row = damage_table[move.id]
            gain = sum(
                max(0.0, row[opponent_id] - best_per_opponent[opponent_id])
                for opponent_id in best_per_opponent
            )
            if gain > best_gain:
                best_gain = gain
                best_move = move

        if best_move is None:
            break  # nothing left adds any further coverage

        chosen.append(best_move)
        row = damage_table[best_move.id]
        for opponent_id in best_per_opponent:
            best_per_opponent[opponent_id] = max(best_per_opponent[opponent_id], row[opponent_id])
        remaining.remove(best_move)

    if remaining and len(chosen) < max_moves:
        remaining.sort(key=lambda move: max(damage_table[move.id].values()), reverse=True)
        chosen.extend(remaining[: max_moves - len(chosen)])

    return chosen


def _bulk_load_movepools(db: Session, pokemon_ids: list[int]) -> dict[int, list[Move]]:
    """{pokemon_id: [learnable Move objects]} for a set of candidates, in one
    query — the N+1 this guards against is real: scoring the ~1187-strong
    legal candidate pool one movepool-query-per-candidate at a time would be
    ~1187 round trips instead of one."""
    if not pokemon_ids:
        return {}
    rows = db.execute(
        select(PokemonMovepool.pokemon_id, Move)
        .join(Move, Move.id == PokemonMovepool.move_id)
        .where(PokemonMovepool.pokemon_id.in_(pokemon_ids))
    ).all()
    movepool_by_pokemon: dict[int, list[Move]] = {}
    for pokemon_id, move in rows:
        movepool_by_pokemon.setdefault(pokemon_id, []).append(move)
    return movepool_by_pokemon


def generate_matchup_counter_team(
    db: Session, opponent_roster: list[BattleRosterSlot], team_size: int
) -> list[TeamPokemonRead]:
    """Stage D: wire Stages A-C into the actual generator POST /api/counter-team
    calls.

    Candidate pool = every legal Pokemon form (is_battle_only=False, so no
    mega/primal/battle-only forms — see Pokemon.is_battle_only). Deliberately
    *not* deduped to one form per species here — Rotom and Rotom-Wash are
    both scored as independent candidates, since they have genuinely
    different types/stats and either could be the better answer depending
    on the opponent roster. One-form-per-species is still enforced, just
    downstream in select_counter_team (Stage B), which picks based on
    actual fitness rather than an arbitrary form ordering, and correctly
    drops sibling forms once one is chosen.

    Also matches real VGC's species clause exactly: uniqueness is enforced
    only *within* a single team, never across both sides — a mirror matchup
    where the opponent's species is also a legal candidate here is real,
    legal competitive play, not excluded.
    """
    type_matrix = fetch_full_type_matrix(db)

    candidates = list(
        db.scalars(
            select(Pokemon)
            .options(selectinload(Pokemon.species))
            .where(Pokemon.is_battle_only.is_(False))
            .order_by(Pokemon.id)
        )
    )

    movepool_by_pokemon = _bulk_load_movepools(db, [p.id for p in candidates])

    scores = [
        score_candidate(
            candidate, movepool_by_pokemon.get(candidate.id, []), opponent_roster, type_matrix
        )
        for candidate in candidates
    ]

    chosen = select_counter_team(scores, team_size)

    roster: list[TeamPokemonRead] = []
    for slot, candidate_score in enumerate(chosen):
        movepool = movepool_by_pokemon.get(candidate_score.pokemon.id, [])
        moves = select_moves_for_coverage(
            movepool, opponent_roster, candidate_score.movepool_damage_table
        )
        roster.append(
            TeamPokemonRead(
                slot=slot,
                pokemon=PokemonRead.model_validate(candidate_score.pokemon),
                moves=[MoveRead.model_validate(m) for m in moves],
            )
        )

    return roster
