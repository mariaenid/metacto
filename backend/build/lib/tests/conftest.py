"""Pytest fixtures shared across unit / integration / e2e suites."""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
