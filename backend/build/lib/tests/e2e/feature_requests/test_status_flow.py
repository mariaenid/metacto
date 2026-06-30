"""End-to-end tests for PATCH /v1/feature-requests/{id}/status."""
from __future__ import annotations

import pytest

from apps.feature_requests.infrastructure.models import FeatureRequestRecord
from apps.identity.infrastructure.models import EmailVerificationTokenRecord, UserRecord


VALID_PASSWORD = "CorrectHorseBattery!7"


def _register_and_authenticate(api_client, email: str, *, role: str = "user") -> str:
    api_client.post(
        "/v1/auth/register",
        {"email": email, "display_name": email.split("@")[0], "password": VALID_PASSWORD},
        format="json",
    )
    token = EmailVerificationTokenRecord.objects.latest("created_at").token
    api_client.post("/v1/auth/verify-email", {"token": token}, format="json")
    if role != "user":
        UserRecord.objects.filter(email=email).update(role=role)
    response = api_client.post(
        "/v1/auth/login", {"email": email, "password": VALID_PASSWORD}, format="json"
    )
    return response.data["access"]


def _submit_fr(api_client, access: str, *, title: str = "Test feature") -> dict:
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    response = api_client.post(
        "/v1/feature-requests",
        {"title": title, "description": ""},
        format="json",
    )
    api_client.credentials()
    return response.data


@pytest.mark.e2e
@pytest.mark.django_db
class TestStatusTransition:
    def test_moderator_can_transition(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_s@example.com")
        fr = _submit_fr(api_client, author_access)

        mod_access = _register_and_authenticate(api_client, "mod_s@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "under_review"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["feature_request"]["status"] == "under_review"
        assert response.data["log"]["from_status"] == "open"
        assert response.data["log"]["to_status"] == "under_review"

    def test_admin_can_transition(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_a@example.com")
        fr = _submit_fr(api_client, author_access)

        admin_access = _register_and_authenticate(api_client, "admin_a@example.com", role="admin")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "closed", "reason": "not viable"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["feature_request"]["status"] == "closed"
        assert response.data["log"]["reason"] == "not viable"

    def test_regular_user_is_forbidden(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_u@example.com")
        fr = _submit_fr(api_client, author_access)

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "under_review"},
            format="json",
        )
        assert response.status_code == 403

    def test_anonymous_is_unauthorised(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_anon@example.com")
        fr = _submit_fr(api_client, author_access)

        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "under_review"},
            format="json",
        )
        assert response.status_code in (401, 403)

    def test_invalid_transition_returns_422(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_inv@example.com")
        fr = _submit_fr(api_client, author_access)

        mod_access = _register_and_authenticate(api_client, "mod_inv@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "shipped"},  # open→shipped not allowed
            format="json",
        )
        assert response.status_code == 422
        assert response.data["code"] == "invalid_transition"

    def test_stale_expected_from_returns_409(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_stale@example.com")
        fr = _submit_fr(api_client, author_access)
        # Advance status directly in DB to simulate concurrent transition
        FeatureRequestRecord.objects.filter(id=fr["id"]).update(status="under_review")

        mod_access = _register_and_authenticate(api_client, "mod_stale@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "under_review"},  # expected_from is stale
            format="json",
        )
        assert response.status_code == 409
        assert response.data["code"] == "status_conflict"

    def test_duplicate_requires_target_returns_422(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_dup@example.com")
        fr = _submit_fr(api_client, author_access)

        mod_access = _register_and_authenticate(api_client, "mod_dup@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        response = api_client.patch(
            f"/v1/feature-requests/{fr['id']}/status",
            {"expected_from": "open", "to_status": "duplicate"},  # missing duplicate_of_id
            format="json",
        )
        assert response.status_code == 422
        assert response.data["code"] == "duplicate_requires_target"

    def test_missing_feature_request_returns_404(self, api_client) -> None:
        mod_access = _register_and_authenticate(api_client, "mod_404@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        response = api_client.patch(
            "/v1/feature-requests/00000000-0000-0000-0000-000000000000/status",
            {"expected_from": "open", "to_status": "under_review"},
            format="json",
        )
        assert response.status_code == 404

    def test_duplicate_cycle_returns_422(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_cyc@example.com")
        fr_a = _submit_fr(api_client, author_access, title="original cyc")
        fr_b = _submit_fr(api_client, author_access, title="copy cyc")

        mod_access = _register_and_authenticate(api_client, "mod_cyc@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")

        # Mark B as duplicate of A
        api_client.patch(
            f"/v1/feature-requests/{fr_b['id']}/status",
            {"expected_from": "open", "to_status": "duplicate", "duplicate_of_id": fr_a["id"]},
            format="json",
        )

        # Try to mark A as duplicate of B — cycle
        response = api_client.patch(
            f"/v1/feature-requests/{fr_a['id']}/status",
            {"expected_from": "open", "to_status": "duplicate", "duplicate_of_id": fr_b["id"]},
            format="json",
        )
        assert response.status_code == 422
        assert response.data["code"] == "duplicate_cycle"
