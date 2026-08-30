import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    IngestionError,
    Move,
    Pokemon,
    PokemonMovepool,
    PokemonSpecies,
    TypeEffectiveness,
)
from app.services.pokeapi_client import (
    PokeApiFetchError,
    extract_id_from_url,
    fetch_move_detail,
    fetch_move_universe,
    fetch_national_pokedex,
    fetch_pokemon_detail,
    fetch_pokemon_universe,
    fetch_type_detail,
    fetch_type_universe,
)
from app.services.validation import (
    validate_move,
    validate_pokemon,
    validate_species,
    validate_type_matchup,
)

logger = logging.getLogger(__name__)

IngestionSource = Literal["batch", "scan"]

_STAT_NAME_MAP = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special_attack": "special-attack",
    "special_defense": "special-defense",
    "speed": "speed",
}


@dataclass
class IngestResult:
    entity_id: int | None
    status: Literal["written", "rejected"]
    reason: str | None = None


@dataclass
class SyncSummary:
    written: int = 0
    rejected: int = 0
    failed: int = 0


# ---------------------------------------------------------------------------
# transform: raw PokeAPI payload -> our normalized shape
# ---------------------------------------------------------------------------


def transform_pokemon(raw: dict) -> dict:
    """Raw PokeAPI /pokemon/{id} payload -> our normalized shape. Stashes the
    movepool's move ids under `_movepool_move_ids` — a leading-underscore key,
    which _upsert_or_reject strips before writing the Pokemon row, and which
    sync_pokemon then reads to populate pokemon_movepool once the Pokemon
    itself has been written."""
    stats_by_name = {s["stat"]["name"]: s.get("base_stat") for s in raw.get("stats", [])}
    types = [t["type"]["name"] for t in sorted(raw.get("types", []), key=lambda t: t["slot"])]

    sprites = raw.get("sprites") or {}
    artwork = (sprites.get("other") or {}).get("official-artwork") or {}
    sprite_url = artwork.get("front_default") or sprites.get("front_default")

    species_url = (raw.get("species") or {}).get("url")
    species_id = extract_id_from_url(species_url) if species_url else None

    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "species_id": species_id,
        "is_default": bool(raw.get("is_default", False)),
        "sprite_url": sprite_url,
        "types": types,
        "_movepool_move_ids": _extract_movepool_move_ids(raw),
        **{field: stats_by_name.get(api_name) for field, api_name in _STAT_NAME_MAP.items()},
    }


def _extract_movepool_move_ids(raw: dict) -> list[int]:
    move_ids = []
    for entry in raw.get("moves", []):
        url = (entry.get("move") or {}).get("url")
        if not url:
            continue
        try:
            move_ids.append(extract_id_from_url(url))
        except ValueError:
            continue
    return move_ids


def transform_species_entry(species_entry: dict) -> dict:
    """Raw /pokedex/national pokemon_entries[] item -> our normalized shape.
    Never raises — a malformed entry just comes back with missing fields, which
    validate_species then catches, so one bad entry can't blow up the whole sync."""
    species_ref = species_entry.get("pokemon_species") or {}
    url = species_ref.get("url")
    species_id = None
    if url:
        try:
            species_id = extract_id_from_url(url)
        except ValueError:
            species_id = None

    return {
        "id": species_id,
        "name": species_ref.get("name"),
        "national_dex_number": species_entry.get("entry_number"),
    }


def transform_move(raw: dict) -> dict:
    """Raw PokeAPI /move/{id} payload -> our normalized shape."""
    effect_chance = raw.get("effect_chance")
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "type": (raw.get("type") or {}).get("name"),
        "damage_class": (raw.get("damage_class") or {}).get("name"),
        "power": raw.get("power"),
        "accuracy": raw.get("accuracy"),
        "pp": raw.get("pp"),
        "priority": raw.get("priority"),
        "effect_chance": effect_chance,
        "effect_text": _extract_effect_text(raw, effect_chance),
    }


def _extract_effect_text(raw: dict, effect_chance: int | None) -> str | None:
    """PokeAPI's short_effect is in English among several languages, and
    often contains a literal "$effect_chance" token to interpolate with the
    move's actual effect_chance value."""
    for entry in raw.get("effect_entries", []):
        if (entry.get("language") or {}).get("name") != "en":
            continue
        text = entry.get("short_effect")
        if text and effect_chance is not None:
            text = text.replace("$effect_chance", str(effect_chance))
        return text
    return None


def transform_type_matchups(raw: dict, all_type_names: set[str]) -> list[dict]:
    """Raw PokeAPI /type/{id} payload -> one row per *known* defending type
    (not just the ones PokeAPI bothers to list — it only lists non-1x
    relations explicitly, so every other type is implicitly neutral).
    Materializing the full set up front means a lookup is a plain query with
    no "missing row = neutral" special-casing."""
    attacking_type = raw.get("name")
    relations = raw.get("damage_relations") or {}
    double_to = {t["name"] for t in relations.get("double_damage_to", [])}
    half_to = {t["name"] for t in relations.get("half_damage_to", [])}
    no_to = {t["name"] for t in relations.get("no_damage_to", [])}

    rows = []
    for defending_type in all_type_names:
        if defending_type in no_to:
            multiplier = 0.0
        elif defending_type in double_to:
            multiplier = 2.0
        elif defending_type in half_to:
            multiplier = 0.5
        else:
            multiplier = 1.0
        rows.append(
            {
                "attacking_type": attacking_type,
                "defending_type": defending_type,
                "multiplier": multiplier,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# The one piece that was genuinely identical across every sync_* function:
# validate an already-transformed entity, then either log a rejection or
# upsert it by primary key. Everything else (fetch strategy, the loop itself,
# commit cadence, per-entity side effects like movepool population) is
# written out explicitly in each sync_* function below rather than folded
# into a generic engine — those parts differ enough between entities that
# forcing them through shared parameters (fetch_detail_fn, on_written, ...)
# made the actual control flow harder to follow than just reading the loop.
# ---------------------------------------------------------------------------


def _upsert_or_reject(
    db: Session,
    model_cls: type,
    entity_type: str,
    transformed: dict,
    raw: dict,
    validate_fn: Callable[[dict], tuple[bool, str | None]],
    source: IngestionSource,
) -> IngestResult:
    """Does not commit — batch callers (sync_species/sync_moves/sync_pokemon)
    commit periodically across many rows, ingest_pokemon commits once
    immediately. Either way that's the caller's call, not this helper's."""
    is_valid, reason = validate_fn(transformed)
    entity_id = transformed.get("id")

    if not is_valid:
        db.add(
            IngestionError(
                entity_type=entity_type,
                entity_id=str(entity_id or "unknown"),
                source=source,
                reason=reason,
                raw_payload=raw,
            )
        )
        return IngestResult(entity_id=entity_id, status="rejected", reason=reason)

    fields = {k: v for k, v in transformed.items() if not k.startswith("_")}
    existing = db.get(model_cls, entity_id)
    if existing is not None:
        for key, value in fields.items():
            setattr(existing, key, value)
        if hasattr(existing, "last_fetched_at"):
            existing.last_fetched_at = datetime.now(timezone.utc)
    else:
        db.add(model_cls(**fields))

    return IngestResult(entity_id=entity_id, status="written")


def _sync_movepool(db: Session, transformed_pokemon: dict) -> None:
    """Populates pokemon_movepool for one Pokemon from the move ids
    transform_pokemon stashed in `_movepool_move_ids`. Skips any move id not
    already present in `move` (e.g. one that failed validation during
    sync_moves) rather than risk an FK violation, and skips ones already
    recorded so re-running a sync stays idempotent. Doesn't commit, same
    reasoning as _upsert_or_reject."""
    pokemon_id = transformed_pokemon["id"]
    move_ids = transformed_pokemon.get("_movepool_move_ids") or []
    if not move_ids:
        return

    known_move_ids = set(db.scalars(select(Move.id).where(Move.id.in_(move_ids))))
    existing_move_ids = set(
        db.scalars(
            select(PokemonMovepool.move_id).where(PokemonMovepool.pokemon_id == pokemon_id)
        )
    )

    for move_id in known_move_ids - existing_move_ids:
        db.add(PokemonMovepool(pokemon_id=pokemon_id, move_id=move_id))


# ---------------------------------------------------------------------------
# public entry points — each one is a plain, readable loop
# ---------------------------------------------------------------------------


def sync_species(db: Session, source: IngestionSource = "batch") -> SyncSummary:
    """Upserts every national-dex species (~1025 rows) from /pokedex/national
    in one bulk call — no per-entry fetch, the full detail is already in that
    response. Must run before sync_pokemon, since every form's species_id FK
    depends on the row existing here. Commits every 50 rows rather than per
    row or once at the end: per-row would mean 1025 round-trips for data that
    cost a single API call to fetch; once-at-the-end risks losing all
    progress to a crash partway through."""
    entries = fetch_national_pokedex()
    total = len(entries)
    summary = SyncSummary()

    for i, entry in enumerate(entries, start=1):
        transformed = transform_species_entry(entry)
        result = _upsert_or_reject(
            db, PokemonSpecies, "pokemon_species", transformed, entry, validate_species, source
        )

        if result.status == "written":
            summary.written += 1
        else:
            summary.rejected += 1
            logger.warning("species: rejected %s: %s", result.entity_id, result.reason)

        if i % 50 == 0 or i == total:
            db.commit()
            logger.info("species progress: %d/%d", i, total)

    return summary


def sync_types(db: Session, source: IngestionSource = "batch") -> SyncSummary:
    """Upserts the full type-effectiveness matchup chart from /type. Fetches
    every type's detail first — needed to know the complete set of type
    names before any row can be defaulted to a neutral (1x) multiplier — then
    writes one row per (attacking, defending) pair, keyed by that pair rather
    than a single PokeAPI id, so this doesn't reuse _upsert_or_reject (built
    around a single-column primary key lookup)."""
    entries = fetch_type_universe()
    raw_by_type: dict[str, dict] = {}
    for entry in entries:
        try:
            raw_by_type[entry["name"]] = fetch_type_detail(entry["name"])
        except PokeApiFetchError as exc:
            logger.warning("types: skipping %s after fetch failure: %s", entry["name"], exc)

    all_type_names = set(raw_by_type.keys())
    summary = SyncSummary()

    for attacking_type, raw in raw_by_type.items():
        for row in transform_type_matchups(raw, all_type_names):
            is_valid, reason = validate_type_matchup(row)
            if not is_valid:
                summary.rejected += 1
                db.add(
                    IngestionError(
                        entity_type="type_effectiveness",
                        entity_id=f"{row.get('attacking_type')}->{row.get('defending_type')}",
                        source=source,
                        reason=reason,
                        raw_payload=raw,
                    )
                )
                continue

            existing = db.scalars(
                select(TypeEffectiveness).where(
                    TypeEffectiveness.attacking_type == row["attacking_type"],
                    TypeEffectiveness.defending_type == row["defending_type"],
                )
            ).first()
            if existing is not None:
                existing.multiplier = row["multiplier"]
            else:
                db.add(TypeEffectiveness(**row))
            summary.written += 1

        db.commit()
        logger.info("types progress: %s done", attacking_type)

    return summary


def sync_moves(
    db: Session, source: IngestionSource = "batch", limit: int | None = None
) -> SyncSummary:
    """Upserts every move from /move. Unlike species, the index only gives
    names — each move's full detail needs its own request. Must run before
    sync_pokemon, since movepool population needs `move` rows to already
    exist."""
    entries = fetch_move_universe(limit=limit)
    total = len(entries)
    summary = SyncSummary()

    for i, entry in enumerate(entries, start=1):
        try:
            raw = fetch_move_detail(entry["name"])
        except PokeApiFetchError as exc:
            summary.failed += 1
            logger.warning("moves: skipping %s after fetch failure: %s", entry["name"], exc)
            continue

        transformed = transform_move(raw)
        result = _upsert_or_reject(db, Move, "move", transformed, raw, validate_move, source)

        if result.status == "written":
            summary.written += 1
        else:
            summary.rejected += 1
            logger.warning("moves: rejected %s: %s", result.entity_id, result.reason)

        if i % 50 == 0 or i == total:
            db.commit()
            logger.info("moves progress: %d/%d", i, total)

    return summary


def sync_pokemon(
    db: Session, source: IngestionSource = "batch", limit: int | None = None
) -> SyncSummary:
    """Upserts every Pokemon form from /pokemon, plus each one's movepool —
    piggybacking on the same detail fetch already happening here (the `moves`
    array is in the same payload), so it costs no extra requests."""
    entries = fetch_pokemon_universe(limit=limit)
    total = len(entries)
    summary = SyncSummary()

    for i, entry in enumerate(entries, start=1):
        try:
            raw = fetch_pokemon_detail(entry["name"])
        except PokeApiFetchError as exc:
            summary.failed += 1
            logger.warning("pokemon: skipping %s after fetch failure: %s", entry["name"], exc)
            continue

        transformed = transform_pokemon(raw)
        result = _upsert_or_reject(db, Pokemon, "pokemon", transformed, raw, validate_pokemon, source)

        if result.status == "written":
            summary.written += 1
            _sync_movepool(db, transformed)
        else:
            summary.rejected += 1
            logger.warning("pokemon: rejected %s: %s", result.entity_id, result.reason)

        if i % 50 == 0 or i == total:
            db.commit()
            logger.info("pokemon progress: %d/%d", i, total)

    return summary


def ingest_pokemon(identifier: int | str, db: Session, source: IngestionSource) -> IngestResult:
    """Single-Pokemon fetch -> transform -> validate -> write, for the scan
    job's future one-at-a-time re-checks (sync_pokemon covers the
    full-catalog case). Commits immediately — there's no batch here to
    amortize the round-trip against.

    Raises PokeApiFetchError on a transient fetch failure — that's the
    caller's concern (retry/skip at the job level), not a validation failure,
    so it is never logged to ingestion_errors.
    """
    raw = fetch_pokemon_detail(identifier)
    transformed = transform_pokemon(raw)
    result = _upsert_or_reject(db, Pokemon, "pokemon", transformed, raw, validate_pokemon, source)
    if result.status == "written":
        _sync_movepool(db, transformed)
    db.commit()
    return result
