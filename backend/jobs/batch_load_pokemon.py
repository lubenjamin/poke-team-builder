"""One-time full catalog load: fetches every Pokemon from PokeAPI into the local
`pokemon` cache via the shared ingestion pipeline (app/services/ingestion.py).

Usage (from backend/, with the venv active):
    python -m jobs.batch_load_pokemon
    python -m jobs.batch_load_pokemon --limit 50   # fast local testing
"""

import logging

from app.db import SessionLocal
from app.services.ingestion import ingest_pokemon, sync_species
from app.services.pokeapi_client import PokeApiFetchError, fetch_pokemon_universe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(limit: int | None = None) -> None:
    db = SessionLocal()
    species_written, species_rejected = sync_species(db, source="batch")
    logger.info(
        "Synced species from /pokedex/national: %d written, %d rejected (validation)",
        species_written,
        species_rejected,
    )

    pokemon_universe = fetch_pokemon_universe(limit=limit)
    logger.info("Fetched %d pokemon from PokeAPI index", len(pokemon_universe))

    written = rejected = failed = 0
    try:
        for i, pokemon in enumerate(pokemon_universe, start=1):
            name = pokemon["name"]
            try:
                result = ingest_pokemon(name, db, source="batch")
            except PokeApiFetchError as exc:
                failed += 1
                logger.warning("Skipping %s after fetch failure: %s", name, exc)
                continue

            if result.status == "written":
                written += 1
            else:
                rejected += 1
                logger.warning("Rejected %s: %s", name, result.reason)

            if i % 50 == 0 or i == len(pokemon_universe):
                logger.info("Progress: %d/%d", i, len(pokemon_universe))
    finally:
        db.close()

    logger.info(
        "Batch load complete: %d written, %d rejected (validation), %d failed (fetch)",
        written,
        rejected,
        failed,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of pokemon fetched (for testing)"
    )
    args = parser.parse_args()
    run(limit=args.limit)
