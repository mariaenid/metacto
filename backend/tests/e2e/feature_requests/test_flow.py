"""End-to-end HTTP flow for feature requests."""

from __future__ import annotations

import pytest

from apps.feature_requests.infrastructure.models import FeatureRequestRecord
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
    response = api_client.post(
        "/v1/auth/login", {"email": email, "password": VALID_PASSWORD}, format="json"
    )
    return response.data["access"]


@pytest.mark.e2e
@pytest.mark.django_db
class TestSubmit:
    def test_verified_user_can_submit(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "verified@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(
            "/v1/feature-requests",
            {"title": "Dark mode", "description": "Pretty please"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["vote_count"] == 1
        assert response.data["status"] == "open"
        assert FeatureRequestRecord.objects.filter(id=response.data["id"]).exists()

    def test_unverified_user_is_forbidden(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "unverified@example.com", verified=False)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(
            "/v1/feature-requests",
            {"title": "Dark mode", "description": ""},
            format="json",
        )
        assert response.status_code == 403

    def test_anonymous_is_unauthorised(self, api_client) -> None:
        response = api_client.post(
            "/v1/feature-requests",
            {"title": "Dark mode", "description": ""},
            format="json",
        )
        assert response.status_code in (401, 403)


@pytest.mark.e2e
@pytest.mark.django_db
class TestList:
    def _seed_three(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "author@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        for title in ("one", "two", "three"):
            api_client.post(
                "/v1/feature-requests",
                {"title": title, "description": ""},
                format="json",
            )
        api_client.credentials()

    def test_anonymous_can_list(self, api_client) -> None:
        self._seed_three(api_client)
        response = api_client.get("/v1/feature-requests")
        assert response.status_code == 200
        assert response.data["total"] == 3
        assert len(response.data["items"]) == 3

    def test_sort_parameter_is_validated(self, api_client) -> None:
        self._seed_three(api_client)
        response = api_client.get("/v1/feature-requests?sort=bananas")
        assert response.status_code == 400
        assert response.data["code"] == "invalid_sort"

    def test_etag_returns_304_on_match(self, api_client) -> None:
        self._seed_three(api_client)
        first = api_client.get("/v1/feature-requests")
        etag = first.headers["ETag"]
        second = api_client.get("/v1/feature-requests", HTTP_IF_NONE_MATCH=etag)
        assert second.status_code == 304


@pytest.mark.e2e
@pytest.mark.django_db
class TestDetail:
    def test_returns_request_and_etag(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "d@example.com")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        created = api_client.post(
            "/v1/feature-requests",
            {"title": "Detail me", "description": "ok"},
            format="json",
        )
        api_client.credentials()
        response = api_client.get(f"/v1/feature-requests/{created.data['id']}")
        assert response.status_code == 200
        assert response.data["title"] == "Detail me"
        assert "ETag" in response.headers

    def test_missing_returns_404(self, api_client) -> None:
        response = api_client.get("/v1/feature-requests/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
