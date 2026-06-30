"""End-to-end auth flow through the HTTP layer."""
from __future__ import annotations

import pytest

from apps.identity.infrastructure.models import (
    EmailVerificationTokenRecord,
    PasswordResetTokenRecord,
    UserRecord,
)


VALID_PASSWORD = "CorrectHorseBattery!7"


@pytest.mark.e2e
@pytest.mark.django_db
class TestRegistration:
    def test_register_returns_201_and_persists_unverified_user(self, api_client) -> None:
        response = api_client.post(
            "/v1/auth/register",
            {"email": "Maria@Example.com", "display_name": "Maria", "password": VALID_PASSWORD},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["email"] == "maria@example.com"
        assert response.data["email_verified"] is False
        assert UserRecord.objects.filter(email="maria@example.com").exists()

    def test_duplicate_returns_409(self, api_client) -> None:
        payload = {"email": "dup@example.com", "display_name": "D", "password": VALID_PASSWORD}
        api_client.post("/v1/auth/register", payload, format="json")
        response = api_client.post("/v1/auth/register", payload, format="json")
        assert response.status_code == 409
        assert response.data["code"] == "email_taken"

    def test_weak_password_returns_400(self, api_client) -> None:
        response = api_client.post(
            "/v1/auth/register",
            {"email": "weak@example.com", "display_name": "W", "password": "short"},
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "invalid_input"


@pytest.mark.e2e
@pytest.mark.django_db
class TestVerifyEmail:
    def test_verifies_user(self, api_client) -> None:
        api_client.post(
            "/v1/auth/register",
            {"email": "v@example.com", "display_name": "V", "password": VALID_PASSWORD},
            format="json",
        )
        record = EmailVerificationTokenRecord.objects.latest("created_at")
        response = api_client.post(
            "/v1/auth/verify-email", {"token": record.token}, format="json"
        )
        assert response.status_code == 200
        assert response.data["email_verified"] is True

    def test_reusing_token_returns_410(self, api_client) -> None:
        api_client.post(
            "/v1/auth/register",
            {"email": "v2@example.com", "display_name": "V", "password": VALID_PASSWORD},
            format="json",
        )
        token = EmailVerificationTokenRecord.objects.latest("created_at").token
        api_client.post("/v1/auth/verify-email", {"token": token}, format="json")
        response = api_client.post(
            "/v1/auth/verify-email", {"token": token}, format="json"
        )
        assert response.status_code == 410


@pytest.mark.e2e
@pytest.mark.django_db
class TestLoginAndRefresh:
    def _register(self, api_client, email: str = "login@example.com") -> None:
        api_client.post(
            "/v1/auth/register",
            {"email": email, "display_name": "L", "password": VALID_PASSWORD},
            format="json",
        )

    def test_login_returns_token_pair(self, api_client) -> None:
        self._register(api_client)
        response = api_client.post(
            "/v1/auth/login",
            {"email": "login@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["access"]
        assert response.data["refresh"]

    def test_wrong_password_returns_401(self, api_client) -> None:
        self._register(api_client)
        response = api_client.post(
            "/v1/auth/login",
            {"email": "login@example.com", "password": "WrongHorseBattery!9"},
            format="json",
        )
        assert response.status_code == 401
        assert response.data["code"] == "invalid_credentials"

    def test_refresh_rotates_token(self, api_client) -> None:
        self._register(api_client)
        login = api_client.post(
            "/v1/auth/login",
            {"email": "login@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        first_refresh = login.data["refresh"]
        response = api_client.post(
            "/v1/auth/refresh", {"refresh": first_refresh}, format="json"
        )
        assert response.status_code == 200
        assert response.data["refresh"] != first_refresh

    def test_reusing_refresh_returns_401_and_invalidates_family(self, api_client) -> None:
        self._register(api_client)
        login = api_client.post(
            "/v1/auth/login",
            {"email": "login@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        first = login.data["refresh"]
        rotated = api_client.post(
            "/v1/auth/refresh", {"refresh": first}, format="json"
        )
        # Re-presenting the old refresh token must trigger breach detection.
        response = api_client.post(
            "/v1/auth/refresh", {"refresh": first}, format="json"
        )
        assert response.status_code == 401
        assert response.data["code"] == "token_reused"
        # And the rotated token, which shared the family, must now also be dead.
        followup = api_client.post(
            "/v1/auth/refresh", {"refresh": rotated.data["refresh"]}, format="json"
        )
        assert followup.status_code == 401


@pytest.mark.e2e
@pytest.mark.django_db
class TestPasswordReset:
    def test_full_flow(self, api_client) -> None:
        api_client.post(
            "/v1/auth/register",
            {"email": "r@example.com", "display_name": "R", "password": VALID_PASSWORD},
            format="json",
        )
        api_client.post(
            "/v1/auth/password-reset/request",
            {"email": "r@example.com"},
            format="json",
        )
        token = PasswordResetTokenRecord.objects.latest("created_at").token
        response = api_client.post(
            "/v1/auth/password-reset/confirm",
            {"token": token, "new_password": "BrandNewHorseBattery!42"},
            format="json",
        )
        assert response.status_code == 204
        # Old password no longer works.
        old_login = api_client.post(
            "/v1/auth/login",
            {"email": "r@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        assert old_login.status_code == 401
        # New password does.
        new_login = api_client.post(
            "/v1/auth/login",
            {"email": "r@example.com", "password": "BrandNewHorseBattery!42"},
            format="json",
        )
        assert new_login.status_code == 200

    def test_unknown_email_returns_202_silently(self, api_client) -> None:
        response = api_client.post(
            "/v1/auth/password-reset/request",
            {"email": "ghost@example.com"},
            format="json",
        )
        # Must NOT reveal whether the email is registered.
        assert response.status_code == 202
