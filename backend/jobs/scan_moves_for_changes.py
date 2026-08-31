"""Recurring change-detection scan: re-fetches every cached Move from
PokeAPI, diffs it against what's cached, and writes move_change_log +
alerts rows for anything that changed (one alert per team-slot that has the
changed move equipped). Move counterpart to jobs/scan_pokemon_for_changes.py
— independent route/job/schedule, since Pokemon and move data have
different real-world PokeAPI update cadences.

Usage (from backend/, with the venv active):
    python -m jobs.scan_moves_for_changes
    python -m jobs.scan_moves_for_changes --limit 20        # fast local/demo run
    python -m jobs.scan_moves_for_changes --max-workers 25   # tune fetch concurrency

`run()` is also called directly by app/routers/internal.py, so the same
function backs both the GitHub Actions cron and the /dev-tools page.
"""

import logging
import time

from app.db import SessionLocal
from app.services.change_detection import (
    DEFAULT_MAX_WORKERS,
    ScanResult,
    scan_all_moves_for_changes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(limit: int | None = None, max_workers: int = DEFAULT_MAX_WORKERS) -> ScanResult:
    db = SessionLocal()
    try:
        started = time.perf_counter()
        result = scan_all_moves_for_changes(db, limit=limit, max_workers=max_workers)
        elapsed = time.perf_counter() - started
        logger.info(
            "scan complete in %.1fs: %d scanned, %d changed, %d change-log rows, "
            "%d alerts created, %d fetch failed",
            elapsed,
            result.scanned,
            result.changed,
            result.changes_logged,
            result.alerts_created,
            result.fetch_failed,
        )
        return result
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of moves re-scanned (for fast local/demo runs)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help="Max concurrent PokeAPI fetches (default: %(default)s)",
    )
    args = parser.parse_args()
    run(limit=args.limit, max_workers=args.max_workers)
