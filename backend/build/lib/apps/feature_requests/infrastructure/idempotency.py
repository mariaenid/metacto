"""Django-cache-backed idempotency store. Backend is Redis in dev/prod, LocMem in tests."""
from __future__ import annotations

from typing import Any

from django.core.cache import cache

IDEMPOTENCY_TTL_SECONDS = 60 * 60 * 24  # 24 hours per RULE-10


class CachedIdempotencyStore:
    def get(self, key: str) -> Any | None:
        return cache.get(key)

    def put(self, key: str, value: Any) -> None:
        cache.set(key, value, IDEMPOTENCY_TTL_SECONDS)
