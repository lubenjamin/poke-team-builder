# Schema & API Reference

See `.claude/CLAUDE.md` for full design rationale. This file is the quick-reference
version: ERD summary and endpoint contract, kept in sync with `backend/app/models/`
and `backend/app/routers/`.

## Tables (v1)

| Table | Purpose | Key relationships |
|---|---|---|
| `pokemon` | Local cache of PokeAPI data; `id` = PokeAPI id | referenced by `team_pokemon`, `pokemon_change_log`, `alerts` |
| `teams` | A client's saved teams | `client_id` (owner key, from `X-Client-Id` header) |
| `team_pokemon` | Ordered roster join table | FK `team_id` → `teams` (cascade delete), FK `pokemon_id` → `pokemon`; unique on `(team_id, slot)` |
| `pokemon_change_log` | Append-only diff record from the scan job | FK `pokemon_id` → `pokemon` |
| `alerts` | Materialized per-client notification of a change | FK → `teams`, `pokemon`, `pokemon_change_log` |
| `ingestion_errors` | Validation failures during ingestion (not transient fetch errors) | none |

## Alert read-time filtering

Alerts are written once by the scan job but must be filtered against **current**
team membership at read time — removing the affected Pokémon from a team hides
the alert even though the underlying `pokemon_change_log` row (and public change
log) is untouched. See `backend/app/routers/alerts.py` for the query.

## Endpoint contract

See `.claude/CLAUDE.md` §7 for the full list. Status as of scaffolding:

- **Implemented (real DB-backed logic):** `pokemon` (list/get), `teams` (full CRUD +
  roster replace), `alerts` (list/dismiss), `changes` (list).
- **Stubbed (501, contract only):** `counter-team` generation (algorithm
  intentionally deferred — open-ended per the assignment), `internal/scan-for-changes`
  (waits on the ingestion pipeline in `services/`).

## Not yet built

- `services/pokeapi_client.py`, `validation.py`, `ingestion.py`, `change_detection.py`,
  `counter_team.py`
- `jobs/batch_load.py`, `jobs/scan_for_changes.py`
- Frontend (`frontend/`)
