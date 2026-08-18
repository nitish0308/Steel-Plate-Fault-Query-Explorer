"""Redis cache-aside helpers for expensive read-only aggregate queries.

Case study: "Faults by Type" and "Largest Defects" scan/aggregate the whole
`plate_faults` table on every request, but the underlying data only changes
when an inspector corrects or discards a record (the PUT/DELETE endpoints).
Caching the result and invalidating it on write is the standard
"cache-aside" pattern used to keep manufacturing dashboards fast without
serving stale counts after a correction.
"""

import json
import os
from typing import Any

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = 60

FAULTS_BY_TYPE_KEY = "cache:faults-by-type"
TOP_DEFECTS_PREFIX = "cache:top-defects"

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def top_defects_key(n: int) -> str:
    return f"{TOP_DEFECTS_PREFIX}:n={n}"


def cache_get(key: str) -> list[dict[str, Any]] | None:
    raw = get_client().get(key)
    return json.loads(raw) if raw is not None else None


def cache_set(key: str, value: list[dict[str, Any]]) -> None:
    get_client().set(key, json.dumps(value), ex=CACHE_TTL_SECONDS)


def cache_invalidate(pattern: str) -> None:
    """Delete every key matching `pattern` (exact key or a `prefix:*` glob)."""
    client = get_client()
    keys = list(client.scan_iter(match=pattern))
    if keys:
        client.delete(*keys)
