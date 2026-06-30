"""End-to-end vote toggle through the HTTP layer."""
from __future__ import annotations

import pytest

from apps.identity.infrastructure.models import EmailVerificationTokenRecord


VALID_PASSWORD = "CorrectHorseBattery!7"


def _register_and_authenticate(api_client, email: str, *, verified: bool = True) -> str:
    api_client.post(
        "/v1/auth/register",
        {"email": email, "display_name": email.split("@")[0], "password": VALID_PASSWORD},
        format="json",
    )
    if verified:
        token = EmailVerificationTokenRecord.objects.latest("created_at").token
        api_client.post("/v1/auth/verify-email", {"token": token}, format="json")
    login = api_client.post(
        "/v1/auth/login", {"email": email, "password": VALID_PASSWORD}, format="json"
    )
    return login.data["access"]


def _submit_request(api_client, email: str = "author@example.com") -> str:
    access = _register_and_authenticate(api_client, email)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api_client.post(
        "/v1/feature-requests",
        {"title": "vote me", "description": ""},
        format="json",
    )
    api_client.credentials()
    return response.data["id"]


@pytest.mark.e2e
@pytest.mark.django_db
class TestCastVote:
    def test_verified_voter_can_cast(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(api_client, "voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(f"/v1/feature-requests/{request_id}/vote")
        assert response.status_code == 200
        assert response.data["voted"] is True
        assert response.data["vote_count"] == 2

    def test_unverified_voter_is_forbidden(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(
            api_client, "unverified-voter@example.com", verified=False
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(f"/v1/feature-requests/{request_id}/vote")
        assert response.status_code == 403

    def test_duplicate_post_is_idempotent(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(api_client, "dup-voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        first = api_client.post(f"/v1/feature-requests/{request_id}/vote")
        second = api_client.post(f"/v1/feature-requests/{request_id}/vote")
        assert first.data["vote_count"] == second.data["vote_count"] == 2

    def test_idempotency_key_returns_cached_response(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(api_client, "idem-voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        first = api_client.post(
            f"/v1/feature-requests/{request_id}/vote",
            HTTP_IDEMPOTENCY_KEY="abc-123",
        )
        # Retract underneath so the live state differs from the cached one.
        api_client.delete(f"/v1/feature-requests/{request_id}/vote")
        replay = api_client.post(
            f"/v1/feature-requests/{request_id}/vote",
            HTTP_IDEMPOTENCY_KEY="abc-123",
        )
        assert replay.data == first.data

    def test_unknown_request_returns_404(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "ghost-voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(
            "/v1/feature-requests/00000000-0000-0000-0000-000000000000/vote"
        )
        assert response.status_code == 404


@pytest.mark.e2e
@pytest.mark.django_db
class TestRetract:
    def test_retract_decrements_count(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(api_client, "retract-voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        api_client.post(f"/v1/feature-requests/{request_id}/vote")
        response = api_client.delete(f"/v1/feature-requests/{request_id}/vote")
        assert response.status_code == 200
        assert response.data["voted"] is False
        assert response.data["vote_count"] == 1

    def test_retract_is_idempotent(self, api_client) -> None:
        request_id = _submit_request(api_client)
        access = _register_and_authenticate(api_client, "retract2-voter@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        first = api_client.delete(f"/v1/feature-requests/{request_id}/vote")
        second = api_client.delete(f"/v1/feature-requests/{request_id}/vote")
        assert first.data["vote_count"] == second.data["vote_count"] == 1
