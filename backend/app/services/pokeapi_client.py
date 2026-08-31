from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

_client = httpx.Client(base_url=POKEAPI_BASE_URL, timeout=10.0)


class PokeApiFetchError(Exception):
    """A PokeAPI request failed after retries were exhausted (network error, 5xx, or
    429 rate limit). Distinct from a validation failure — callers should skip and
    log, not write to ingestion_errors (see services/ingestion.py)."""


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    return False


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _get(path: str) -> dict:
    response = _client.get(path)
    response.raise_for_status()
    return response.json()


def fetch_pokemon_universe(limit: int | None = None) -> list[dict]:
    """Returns [{"name": ..., "url": ...}, ...] from the PokeAPI index. PokeAPI
    returns the full set in one page as long as `limit` >= total count."""
    page_size = limit if limit is not None else 100_000
    try:
        data = _get(f"/pokemon?limit={page_size}&offset=0")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch pokemon index: {exc}") from exc
    return data["results"]


def fetch_pokemon_detail(identifier: int | str) -> dict:
    try:
        return _get(f"/pokemon/{identifier}")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch pokemon {identifier!r}: {exc}") from exc


def fetch_pokemon_details_concurrently(
    identifiers: list[int], max_workers: int = 15
) -> dict[int, dict | PokeApiFetchError]:
    """Fetches many Pokemon details in parallel via a thread pool — httpx's
    Client is thread-safe and releases the GIL during the actual network
    wait, so this gets real concurrency without an async rewrite of the
    client or anything built on top of it. Bounded by max_workers to stay a
    reasonable citizen of a public API with no documented rate-limit SLA.

    Returns one entry per identifier: either the raw payload, or the
    PokeApiFetchError that identifier failed with (after its own retries
    were exhausted) — a caller should skip that one id rather than let it
    abort the whole batch, same as every sequential fetch_pokemon_detail
    caller already does."""
    results: dict[int, dict | PokeApiFetchError] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(fetch_pokemon_detail, identifier): identifier
            for identifier in identifiers
        }
        for future in as_completed(future_to_id):
            identifier = future_to_id[future]
            try:
                results[identifier] = future.result()
            except PokeApiFetchError as exc:
                results[identifier] = exc
    return results


def fetch_national_pokedex() -> list[dict]:
    """Returns pokemon_entries from /pokedex/national:
    [{"entry_number": 1, "pokemon_species": {"name": "bulbasaur", "url": "..."}}, ...]
    This is the authoritative source for national dex numbers — species ids don't
    reliably line up with dex numbers for every entry."""
    try:
        data = _get("/pokedex/national")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch national pokedex: {exc}") from exc
    return data["pokemon_entries"]

def fetch_move_universe(limit: int | None = None) -> list[dict]:
    """Returns [{"name": ..., "url": ...}, ...] from the PokeAPI move index. PokeAPI
    returns the full move set in one page as long as `limit` >= total count."""
    page_size = limit if limit is not None else 100_000
    try:
        data = _get(f"/move?limit={page_size}&offset=0")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch move index: {exc}") from exc
    return data["results"]

def fetch_move_detail(identifier: int | str) -> dict:
    try:
        return _get(f"/move/{identifier}")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch move {identifier!r}: {exc}") from exc


def fetch_move_details_concurrently(
    identifiers: list[int], max_workers: int = 15
) -> dict[int, dict | PokeApiFetchError]:
    """Move counterpart to fetch_pokemon_details_concurrently — same bounded
    thread-pool shape, see its docstring for the reasoning."""
    results: dict[int, dict | PokeApiFetchError] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(fetch_move_detail, identifier): identifier
            for identifier in identifiers
        }
        for future in as_completed(future_to_id):
            identifier = future_to_id[future]
            try:
                results[identifier] = future.result()
            except PokeApiFetchError as exc:
                results[identifier] = exc
    return results


def fetch_type_universe() -> list[dict]:
    """Returns [{"name": ..., "url": ...}, ...] from the PokeAPI type index
    (~20 entries, including a couple of non-battle pseudo-types like "unknown"
    and "shadow" — harmless, nothing in our data references them as a real
    type). No limit param — small enough to always fetch in full."""
    try:
        data = _get("/type?limit=100&offset=0")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch type index: {exc}") from exc
    return data["results"]


def fetch_type_detail(identifier: int | str) -> dict:
    try:
        return _get(f"/type/{identifier}")
    except (httpx.TransportError, httpx.HTTPStatusError) as exc:
        raise PokeApiFetchError(f"Failed to fetch type {identifier!r}: {exc}") from exc


def extract_id_from_url(url: str) -> int:
    """PokeAPI resource URLs end in '.../<id>/' — pull the id out."""
    return int(url.rstrip("/").rsplit("/", 1)[-1])
