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
