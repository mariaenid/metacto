"""Pytest fixtures shared across unit / integration / e2e suites."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def reset_cache():
    # Clear throttle counters between tests so rate-limit state doesn't bleed.
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
