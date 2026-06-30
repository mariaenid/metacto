"""End-to-end tests for GET /v1/admin/stats."""

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


@pytest.mark.e2e
@pytest.mark.django_db
class TestAdminStats:
    def test_admin_receives_full_stats_shape(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_st@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        api_client.post(
            "/v1/feature-requests",
            {"title": "Stats test", "description": ""},
            format="json",
        )
        api_client.credentials()

        admin_access = _register_and_authenticate(api_client, "admin_st@example.com", role="admin")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        response = api_client.get("/v1/admin/stats")

        assert response.status_code == 200
        data = response.data
        assert "counts_by_status" in data
        assert "activity_30d" in data
        assert "triage" in data
        assert "top_voted" in data

        assert "open" in data["counts_by_status"]
        assert data["counts_by_status"]["open"] >= 1

        assert data["activity_30d"]["submissions"] >= 1
        assert "votes" in data["activity_30d"]
        assert "transitions" in data["activity_30d"]

        assert "oldest_open_at" in data["triage"]
        assert "stale_under_review_count" in data["triage"]
        assert data["triage"]["oldest_open_at"] is not None

        assert isinstance(data["top_voted"], list)

    def test_regular_user_is_forbidden(self, api_client) -> None:
        user_access = _register_and_authenticate(api_client, "user_st@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_access}")
        assert api_client.get("/v1/admin/stats").status_code == 403

    def test_moderator_is_forbidden(self, api_client) -> None:
        mod_access = _register_and_authenticate(api_client, "mod_st@example.com", role="moderator")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        assert api_client.get("/v1/admin/stats").status_code == 403

    def test_anonymous_is_unauthorised(self, api_client) -> None:
        assert api_client.get("/v1/admin/stats").status_code in (401, 403)

    def test_top_voted_only_shows_active_statuses(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "author_tv@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        response = api_client.post(
            "/v1/feature-requests",
            {"title": "Should appear", "description": ""},
            format="json",
        )
        fr_id = response.data["id"]
        # Ship the request — should no longer appear in top_voted
        FeatureRequestRecord.objects.filter(id=fr_id).update(status="shipped", vote_count=9999)
        api_client.credentials()

        admin_access = _register_and_authenticate(api_client, "admin_tv@example.com", role="admin")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_access}")
        stats = api_client.get("/v1/admin/stats").data

        top_ids = {r["id"] for r in stats["top_voted"]}
        assert fr_id not in top_ids
