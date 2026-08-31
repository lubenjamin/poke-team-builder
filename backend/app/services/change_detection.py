import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Alert,
    IngestionError,
    Move,
    MoveChangeLog,
    Pokemon,
    PokemonChangeLog,
    PokemonMovepool,
    Team,
    TeamPokemon,
    TeamPokemonMove,
)
from app.services.ingestion import (
    ingest_pokemon,
    sync_movepool,
    transform_move,
    transform_pokemon,
)
from app.services.pokeapi_client import (
    PokeApiFetchError,
    fetch_move_details_concurrently,
    fetch_pokemon_details_concurrently,
)
from app.services.validation import validate_move, validate_pokemon

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKERS = 15

# Fetching the *entire* catalog concurrently before writing any of it (the
# original design) held every raw PokeAPI payload for the whole catalog in
# memory at once — confirmed live to OOM-kill a 512MB Render instance on a
# full ~1343-Pokemon scan. Processing in bounded batches (fetch a batch,
# write it, commit, discard it, move on) keeps peak memory roughly constant
# regardless of catalog size, while still covering every single entry on
# every scan run — nothing is skipped or rotated out.
DEFAULT_SCAN_BATCH_SIZE = 50

# The Pokemon fields that actually surface in the app (Pokedex grid, team
# builder, detail page) — a change to any of these is worth alerting a user
# whose team includes that Pokemon about. species_id/is_default/last_fetched_at
# are internal bookkeeping, not user-visible data, so they're excluded.
_TRACKED_FIELDS = (
    "name",
    "sprite_url",
    "types",
    "hp",
    "attack",
    "defense",
    "special_attack",
    "special_defense",
    "speed",
)

# Same idea, for Move — everything gameplay-relevant except id.
_TRACKED_MOVE_FIELDS = (
    "name",
    "type",
    "damage_class",
    "power",
    "accuracy",
    "pp",
    "priority",
    "effect_chance",
    "effect_text",
)


@dataclass
class ScanResult:
    scanned: int = 0
    changed: int = 0
    changes_logged: int = 0
    alerts_created: int = 0
    fetch_failed: int = 0


def _snapshot(entity: object, fields: tuple[str, ...]) -> dict[str, str]:
    return {field: _stringify(getattr(entity, field)) for field in fields}


def _stringify(value: object) -> str:
    return ", ".join(value) if isinstance(value, list) else str(value)


# ---------------------------------------------------------------------------
# Single-item manual/CLI checks — fetches synchronously, one at a time.
# Only diffs display fields (not movepool); the full-catalog scan below is
# the feature-complete path.
# ---------------------------------------------------------------------------


def scan_pokemon_for_changes(db: Session, pokemon_id: int) -> list[PokemonChangeLog]:
    """Re-fetches one Pokemon through the existing ingestion pipeline
    (ingest_pokemon), diffs its tracked fields against what was cached
    beforehand, and for every changed field writes a PokemonChangeLog row
    plus an Alert row per client whose team currently holds that Pokemon.

    Returns the newly-written change log rows — empty if nothing changed, or
    if the Pokemon wasn't cached yet (nothing to diff against on a first
    sighting, so no false "changes" on the very first scan)."""
    before = db.get(Pokemon, pokemon_id)
    before_snapshot = _snapshot(before, _TRACKED_FIELDS) if before is not None else None

    ingest_pokemon(pokemon_id, db, source="scan")

    return _diff_and_record(db, pokemon_id, before_snapshot)


def _diff_and_record(
    db: Session, pokemon_id: int, before_snapshot: dict[str, str] | None, commit: bool = True
) -> list[PokemonChangeLog]:
    """Shared tail end of scan_pokemon_for_changes: diff the now-current
    cached row against the pre-fetch snapshot, and for every changed field
    write a PokemonChangeLog + one Alert per affected client. Assumes the
    row has already been re-ingested (written) by the caller."""
    after = db.get(Pokemon, pokemon_id)
    if before_snapshot is None or after is None:
        return []

    after_snapshot = _snapshot(after, _TRACKED_FIELDS)
    changed_fields = [f for f in _TRACKED_FIELDS if before_snapshot[f] != after_snapshot[f]]
    if not changed_fields:
        return []

    logs = [
        PokemonChangeLog(
            pokemon_id=pokemon_id,
            field_name=field,
            old_value=before_snapshot[field],
            new_value=after_snapshot[field],
        )
        for field in changed_fields
    ]
    db.add_all(logs)
    db.flush()  # assign ids so alerts below can FK to them — cheap relative to a commit

    _generate_alerts(db, pokemon_id, logs)
    if commit:
        db.commit()
    return logs


def _generate_alerts(db: Session, pokemon_id: int, logs: list[PokemonChangeLog]) -> None:
    """One alert per client currently holding this Pokemon on any team,
    per changed field — looked up via team_pokemon at detection time (the
    same join alerts.py re-checks at read time, so an alert still
    disappears if the Pokemon is later removed from the team)."""
    affected_teams = db.execute(
        select(Team.id, Team.client_id)
        .join(TeamPokemon, TeamPokemon.team_id == Team.id)
        .where(TeamPokemon.pokemon_id == pokemon_id)
    ).all()
    if not affected_teams:
        return

    for log in logs:
        message = (
            f"{log.field_name.replace('_', ' ')} changed from "
            f'"{log.old_value}" to "{log.new_value}"'
        )
        for team_id, client_id in affected_teams:
            db.add(
                Alert(
                    client_id=client_id,
                    team_id=team_id,
                    pokemon_id=pokemon_id,
                    pokemon_change_log_id=log.id,
                    message=message,
                )
            )


# ---------------------------------------------------------------------------
# Full-catalog Pokemon scan — compare-before-write, concurrent fetch.
# ---------------------------------------------------------------------------


def _scan_one_pokemon(
    db: Session,
    pokemon_id: int,
    raw: dict,
    before_snapshot: dict[str, str],
    before_movepool_ids: set[int],
    source: str,
) -> list[PokemonChangeLog]:
    """Compare-before-write for one Pokemon: transform + validate always run
    (cheap, no DB); an invalid payload is logged and rejected regardless of
    whether it happens to look "unchanged". If valid, diff tracked fields
    and movepool against the pre-fetch snapshot — if NEITHER differs, return
    immediately with no DB write at all (the common case on a scan run).
    Otherwise write only what changed: scalar fields (+ last_fetched_at) if
    fields changed; movepool (bidirectionally) if it changed, logging a
    PokemonChangeLog row per move gained or lost — the public record of it,
    independent of whether anyone has that move equipped — and, for any
    removed move, also unassigning it from every team that has it equipped
    and alerting the owner; and PokemonChangeLog + alerts for changed
    display fields."""
    transformed = transform_pokemon(raw)
    is_valid, reason = validate_pokemon(transformed)
    if not is_valid:
        db.add(
            IngestionError(
                entity_type="pokemon",
                entity_id=str(transformed.get("id") or pokemon_id),
                source=source,
                reason=reason,
                raw_payload=raw,
            )
        )
        return []

    fetched_snapshot = {f: _stringify(transformed.get(f)) for f in _TRACKED_FIELDS}
    fetched_movepool_ids = set(transformed.get("_movepool_move_ids") or [])

    changed_fields = [f for f in _TRACKED_FIELDS if fetched_snapshot[f] != before_snapshot[f]]
    movepool_changed = fetched_movepool_ids != before_movepool_ids

    if not changed_fields and not movepool_changed:
        return []

    if changed_fields:
        existing = db.get(Pokemon, pokemon_id)
        fields = {k: v for k, v in transformed.items() if not k.startswith("_")}
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.last_fetched_at = datetime.now(timezone.utc)

    movepool_logs: list[PokemonChangeLog] = []
    if movepool_changed:
        added, removed = sync_movepool(db, transformed, existing_move_ids=before_movepool_ids)
        movepool_logs = _record_movepool_changes(db, pokemon_id, added, removed)
        if removed:
            _handle_movepool_removals(db, pokemon_id, removed)

    field_logs: list[PokemonChangeLog] = []
    if changed_fields:
        field_logs = [
            PokemonChangeLog(
                pokemon_id=pokemon_id,
                field_name=field,
                old_value=before_snapshot[field],
                new_value=fetched_snapshot[field],
            )
            for field in changed_fields
        ]
        db.add_all(field_logs)
        db.flush()
        _generate_alerts(db, pokemon_id, field_logs)

    return field_logs + movepool_logs


def _record_movepool_changes(
    db: Session, pokemon_id: int, added: set[int], removed: set[int]
) -> list[PokemonChangeLog]:
    """One PokemonChangeLog row per move gained or lost — the public record
    of a movepool change. Separate from _handle_movepool_removals, which
    answers the narrower "does a team need repairing + its owner alerted"
    question only for moves that are actually equipped; this logs every
    movepool change regardless."""
    if not added and not removed:
        return []

    move_names = {
        move.id: move.name for move in db.scalars(select(Move).where(Move.id.in_(added | removed)))
    }

    logs = [
        PokemonChangeLog(
            pokemon_id=pokemon_id,
            field_name="movepool",
            old_value="not learnable",
            new_value=move_names.get(move_id, f"move {move_id}"),
        )
        for move_id in added
    ] + [
        PokemonChangeLog(
            pokemon_id=pokemon_id,
            field_name="movepool",
            old_value=move_names.get(move_id, f"move {move_id}"),
            new_value="not learnable",
        )
        for move_id in removed
    ]
    db.add_all(logs)
    return logs


def _handle_movepool_removals(db: Session, pokemon_id: int, removed_move_ids: set[int]) -> None:
    """A move that's no longer learnable can't stay assigned to a team slot
    — persisting it would itself be a data-integrity violation. For every
    team-slot that has one of these moves equipped, delete that
    TeamPokemonMove row (the slot goes empty) and alert the owning client."""
    rows = db.execute(
        select(TeamPokemonMove, TeamPokemon.team_id, Team.client_id)
        .join(TeamPokemon, TeamPokemonMove.team_pokemon_id == TeamPokemon.id)
        .join(Team, TeamPokemon.team_id == Team.id)
        .where(TeamPokemon.pokemon_id == pokemon_id, TeamPokemonMove.move_id.in_(removed_move_ids))
    ).all()
    if not rows:
        return

    pokemon = db.get(Pokemon, pokemon_id)
    move_names = {
        move.id: move.name
        for move in db.scalars(select(Move).where(Move.id.in_(removed_move_ids)))
    }

    for team_pokemon_move, team_id, client_id in rows:
        move_name = move_names.get(team_pokemon_move.move_id, "A move")
        db.add(
            Alert(
                client_id=client_id,
                team_id=team_id,
                pokemon_id=pokemon_id,
                move_id=team_pokemon_move.move_id,
                message=(
                    f"{move_name} is no longer learnable by {pokemon.name} — "
                    "it's been removed from your team"
                ),
            )
        )
        db.delete(team_pokemon_move)


def scan_all_pokemon_for_changes(
    db: Session,
    limit: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    batch_size: int = DEFAULT_SCAN_BATCH_SIZE,
) -> ScanResult:
    """Re-scans the cached catalog — the recurring job's entry point (also
    the internal on-demand trigger). Every scan covers the full requested
    set every run (no rotation) since any Pokemon could change and it
    should be caught as soon as possible.

    Processed in bounded batches of `batch_size`, not the whole catalog at
    once: within each batch, phase 1 fetches every targeted Pokemon's fresh
    PokeAPI payload concurrently (pure network I/O, no DB involved), then
    phase 2 diffs and writes each one sequentially against the single DB
    session (SQLAlchemy sessions aren't thread-safe) and commits once for
    the batch. Batching bounds peak memory to roughly one batch's worth of
    raw payloads regardless of catalog size — holding the entire catalog's
    payloads in memory at once (the original design) was confirmed to
    OOM-kill a memory-constrained deployment on a full scan.

    A transient PokeAPI fetch failure just skips that one Pokemon rather
    than aborting the whole run; `limit` caps how many are re-checked, for a
    fast local/demo run instead of the full ~1343-Pokemon catalog."""
    pokemon_ids = list(db.scalars(select(Pokemon.id).order_by(Pokemon.id)))
    if limit is not None:
        pokemon_ids = pokemon_ids[:limit]
    total = len(pokemon_ids)
    started_at = datetime.now(timezone.utc)
    result = ScanResult()

    for batch_start in range(0, total, batch_size):
        batch_ids = pokemon_ids[batch_start : batch_start + batch_size]

        # Snapshot "before" state for just this batch, from the cache as it
        # stood before this batch writes anything — the fetch below is
        # fetch-only, so the cache can't have changed in between. Scoping
        # this per-batch (not the whole catalog up front) is the other half
        # of the memory fix — before_movepool in particular can be sizeable
        # (every learnable move id for every Pokemon in the batch).
        before_snapshots = {
            pokemon.id: _snapshot(pokemon, _TRACKED_FIELDS)
            for pokemon in db.scalars(select(Pokemon).where(Pokemon.id.in_(batch_ids)))
        }
        before_movepool: dict[int, set[int]] = {}
        for pokemon_id, move_id in db.execute(
            select(PokemonMovepool.pokemon_id, PokemonMovepool.move_id).where(
                PokemonMovepool.pokemon_id.in_(batch_ids)
            )
        ).all():
            before_movepool.setdefault(pokemon_id, set()).add(move_id)

        fetched = fetch_pokemon_details_concurrently(batch_ids, max_workers=max_workers)

        for pokemon_id in batch_ids:
            result.scanned += 1
            raw_or_error = fetched[pokemon_id]
            if isinstance(raw_or_error, PokeApiFetchError):
                result.fetch_failed += 1
                logger.warning(
                    "pokemon scan: skipping pokemon %d after fetch failure: %s",
                    pokemon_id,
                    raw_or_error,
                )
                continue

            logs = _scan_one_pokemon(
                db,
                pokemon_id,
                raw_or_error,
                before_snapshots[pokemon_id],
                before_movepool.get(pokemon_id, set()),
                source="scan",
            )

            if logs:
                result.changed += 1
                result.changes_logged += len(logs)

        db.commit()
        # fetched/before_snapshots/before_movepool are reassigned (or fall
        # out of scope) on the next iteration, freeing this batch's memory
        # before the next one is fetched.
        logger.info("pokemon scan progress: %d/%d", min(batch_start + batch_size, total), total)

    result.alerts_created = db.scalar(
        select(func.count(Alert.id)).where(Alert.created_at >= started_at)
    ) or 0
    return result


# ---------------------------------------------------------------------------
# Full-catalog Move scan — same compare-before-write, concurrent-fetch shape.
# ---------------------------------------------------------------------------


def _scan_one_move(
    db: Session, move_id: int, raw: dict, before_snapshot: dict[str, str], source: str
) -> list[MoveChangeLog]:
    transformed = transform_move(raw)
    is_valid, reason = validate_move(transformed)
    if not is_valid:
        db.add(
            IngestionError(
                entity_type="move",
                entity_id=str(transformed.get("id") or move_id),
                source=source,
                reason=reason,
                raw_payload=raw,
            )
        )
        return []

    fetched_snapshot = {f: _stringify(transformed.get(f)) for f in _TRACKED_MOVE_FIELDS}
    changed_fields = [f for f in _TRACKED_MOVE_FIELDS if fetched_snapshot[f] != before_snapshot[f]]
    if not changed_fields:
        return []

    existing = db.get(Move, move_id)
    for key, value in transformed.items():
        setattr(existing, key, value)

    logs = [
        MoveChangeLog(
            move_id=move_id,
            field_name=field,
            old_value=before_snapshot[field],
            new_value=fetched_snapshot[field],
        )
        for field in changed_fields
    ]
    db.add_all(logs)
    db.flush()
    _generate_move_change_alerts(db, move_id, logs)
    return logs


def _generate_move_change_alerts(db: Session, move_id: int, logs: list[MoveChangeLog]) -> None:
    """One alert per (changed field x team-slot that has this move
    equipped) — looked up via team_pokemon_move, unlike Pokemon-field
    alerts which look up via team_pokemon directly (a move's relevance is
    scoped by who has it *equipped*, not just who has the Pokemon)."""
    affected_slots = db.execute(
        select(TeamPokemon.pokemon_id, TeamPokemon.team_id, Team.client_id)
        .select_from(TeamPokemonMove)
        .join(TeamPokemon, TeamPokemonMove.team_pokemon_id == TeamPokemon.id)
        .join(Team, TeamPokemon.team_id == Team.id)
        .where(TeamPokemonMove.move_id == move_id)
    ).all()
    if not affected_slots:
        return

    for log in logs:
        message = (
            f"{log.field_name.replace('_', ' ')} changed from "
            f'"{log.old_value}" to "{log.new_value}"'
        )
        for pokemon_id, team_id, client_id in affected_slots:
            db.add(
                Alert(
                    client_id=client_id,
                    team_id=team_id,
                    pokemon_id=pokemon_id,
                    move_id=move_id,
                    move_change_log_id=log.id,
                    message=message,
                )
            )


def scan_all_moves_for_changes(
    db: Session,
    limit: int | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
    batch_size: int = DEFAULT_SCAN_BATCH_SIZE,
) -> ScanResult:
    """Move counterpart to scan_all_pokemon_for_changes — same bounded-batch
    (fetch a batch concurrently, write it, commit, discard it) shape, run as
    an independent scan/route/job per Pokemon and Move data having
    different real-world PokeAPI update cadences. See
    scan_all_pokemon_for_changes's docstring for why batching matters:
    holding the whole catalog's fetched payloads in memory at once OOM-killed
    a memory-constrained deployment."""
    move_ids = list(db.scalars(select(Move.id).order_by(Move.id)))
    if limit is not None:
        move_ids = move_ids[:limit]
    total = len(move_ids)
    started_at = datetime.now(timezone.utc)
    result = ScanResult()

    for batch_start in range(0, total, batch_size):
        batch_ids = move_ids[batch_start : batch_start + batch_size]

        before_snapshots = {
            move.id: _snapshot(move, _TRACKED_MOVE_FIELDS)
            for move in db.scalars(select(Move).where(Move.id.in_(batch_ids)))
        }

        fetched = fetch_move_details_concurrently(batch_ids, max_workers=max_workers)

        for move_id in batch_ids:
            result.scanned += 1
            raw_or_error = fetched[move_id]
            if isinstance(raw_or_error, PokeApiFetchError):
                result.fetch_failed += 1
                logger.warning(
                    "move scan: skipping move %d after fetch failure: %s", move_id, raw_or_error
                )
                continue

            logs = _scan_one_move(
                db, move_id, raw_or_error, before_snapshots[move_id], source="scan"
            )

            if logs:
                result.changed += 1
                result.changes_logged += len(logs)

        db.commit()
        logger.info("move scan progress: %d/%d", min(batch_start + batch_size, total), total)

    result.alerts_created = db.scalar(
        select(func.count(Alert.id)).where(Alert.created_at >= started_at)
    ) or 0
    return result
