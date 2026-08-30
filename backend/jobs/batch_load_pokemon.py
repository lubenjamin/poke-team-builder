"""One-time full catalog load: species, type matchups, moves, and every
Pokemon form, via the shared ingestion pipeline (app/services/ingestion.py).
Species and moves must be synced before pokemon (pokemon.species_id and
pokemon_movepool.move_id both FK into them) — types has no such dependency,
included here just for one-command convenience.

Usage (from backend/, with the venv active):
    python -m jobs.batch_load_pokemon
    python -m jobs.batch_load_pokemon --limit 50   # fast local testing (caps moves + pokemon)
"""

import logging

from app.db import SessionLocal
from app.services.ingestion import SyncSummary, sync_moves, sync_pokemon, sync_species, sync_types

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _log_summary(label: str, summary: SyncSummary) -> None:
    logger.info(
        "%s complete: %d written, %d rejected (validation), %d failed (fetch)",
        label,
        summary.written,
        summary.rejected,
        summary.failed,
    )


def run(limit: int | None = None) -> None:
    db = SessionLocal()
    try:
        _log_summary("Species", sync_species(db, source="batch"))
        _log_summary("Types", sync_types(db, source="batch"))
        _log_summary("Moves", sync_moves(db, source="batch", limit=limit))
        _log_summary("Pokemon", sync_pokemon(db, source="batch", limit=limit))
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of moves and pokemon fetched (for fast local testing)",
    )
    args = parser.parse_args()
    run(limit=args.limit)
