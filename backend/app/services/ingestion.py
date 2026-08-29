from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.models import IngestionError, Pokemon, PokemonSpecies
from app.services.pokeapi_client import (
    extract_id_from_url,
    fetch_national_pokedex,
    fetch_pokemon_universe,
)
from app.services.validation import validate_pokemon, validate_species

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
    pokemon_id: int | None
    status: Literal["written", "rejected"]
    reason: str | None = None


def transform_pokemon(raw: dict) -> dict:
    """Raw PokeAPI /pokemon/{id} payload -> our normalized shape."""
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
        **{field: stats_by_name.get(api_name) for field, api_name in _STAT_NAME_MAP.items()},
    }


def transform_species_entry(entry: dict) -> dict:
    """Raw /pokedex/national pokemon_entries[] item -> our normalized shape.
    Never raises — a malformed entry just comes back with missing fields, which
    validate_species then catches, so one bad entry can't blow up the whole sync."""
    species_ref = entry.get("pokemon_species") or {}
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
        "national_dex_number": entry.get("entry_number"),
    }


def sync_species(db: Session, source: IngestionSource = "batch") -> tuple[int, int]:
    """Upserts every national-dex species (~1025 rows) from /pokedex/national.
    Must run before ingesting pokemon forms, since each form's species_id FK
    depends on the row existing here. Same fail-closed contract as ingest_pokemon:
    a malformed entry is rejected and logged to ingestion_errors, not written.
    Returns (written, rejected)."""
    pokedex_entries = fetch_national_pokedex()

    written = rejected = 0
    for entry in pokedex_entries:
        transformed = transform_species_entry(entry)
        is_valid, reason = validate_species(transformed)
        if not is_valid:
            rejected += 1
            db.add(
                IngestionError(
                    entity_type="pokemon_species",
                    entity_id=str(
                        transformed.get("id") or entry.get("entry_number") or "unknown"
                    ),
                    source=source,
                    reason=reason,
                    raw_payload=entry,
                )
            )
            continue

        existing = db.get(PokemonSpecies, transformed["id"])
        if existing is not None:
            existing.name = transformed["name"]
            existing.national_dex_number = transformed["national_dex_number"]
        else:
            db.add(PokemonSpecies(**transformed))
        written += 1

    db.commit()
    return written, rejected


def ingest_pokemon(identifier: int | str, db: Session, source: IngestionSource) -> IngestResult:
    """Shared fetch -> transform -> validate -> write pipeline (CLAUDE.md §6),
    used by both jobs/batch_load.py and jobs/scan_for_changes.py.

    Raises PokeApiFetchError on a transient fetch failure — that's the caller's
    concern (retry/skip at the job level), not a validation failure, so it is
    never logged to ingestion_errors.
    """
    raw = fetch_pokemon_universe(identifier)
    transformed = transform_pokemon(raw)

    is_valid, reason = validate_pokemon(transformed)
    if not is_valid:
        db.add(
            IngestionError(
                entity_type="pokemon",
                entity_id=str(transformed.get("id") or identifier),
                source=source,
                reason=reason,
                raw_payload=raw,
            )
        )
        db.commit()
        return IngestResult(pokemon_id=transformed.get("id"), status="rejected", reason=reason)

    existing = db.get(Pokemon, transformed["id"])
    if existing is not None:
        for field, value in transformed.items():
            setattr(existing, field, value)
        existing.last_fetched_at = datetime.now(timezone.utc)
    else:
        db.add(Pokemon(**transformed))

    db.commit()
    return IngestResult(pokemon_id=transformed["id"], status="written")
