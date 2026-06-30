"""Test overrides; uses in-memory caches and a faster password hasher to keep the suite quick."""

from .base import *  # noqa: F403

DEBUG = False

# Speeds the test suite without changing production hashing behaviour.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tests",
    }
}

# Disable throttling in tests — the shared LocMemCache would bleed rate-limit state
# across test cases and cause spurious 429s.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # type: ignore[name-defined]  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

# Skip migration framework in tests — tables are created directly from the ORM models.
# This avoids maintaining migration files during active development and keeps the suite fast.
MIGRATION_MODULES = {
    "identity": None,
    "feature_requests": None,
    "comments": None,
    "auth": None,
    "contenttypes": None,
    "sessions": None,
}
