"""End-to-end tests for comment and timeline endpoints."""

from __future__ import annotations

import pytest

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


def _submit_fr(api_client, access: str) -> str:
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = api_client.post(
        "/v1/feature-requests", {"title": "FR for comments", "description": ""}, format="json"
    )
    api_client.credentials()
    return r.data["id"]


@pytest.mark.e2e
@pytest.mark.django_db
class TestPostComment:
    def test_verified_user_can_post(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "cmt_author@example.com")
        fr_id = _submit_fr(api_client, access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        r = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments",
            {"body": "great idea"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["body"] == "great idea"
        assert not r.data["is_deleted"]

    def test_anonymous_cannot_post(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "cmt_anon_fr@example.com")
        fr_id = _submit_fr(api_client, access)
        r = api_client.post(f"/v1/feature-requests/{fr_id}/comments", {"body": "x"}, format="json")
        assert r.status_code in (401, 403)

    def test_unverified_cannot_post(self, api_client) -> None:
        api_client.post(
            "/v1/auth/register",
            {
                "email": "unverified_cmt@example.com",
                "display_name": "u",
                "password": VALID_PASSWORD,
            },
            format="json",
        )
        r_login = api_client.post(
            "/v1/auth/login",
            {"email": "unverified_cmt@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        access = r_login.data.get("access") or ""
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        r = api_client.post(
            "/v1/feature-requests/00000000-0000-0000-0000-000000000000/comments",
            {"body": "x"},
            format="json",
        )
        assert r.status_code in (401, 403)


@pytest.mark.e2e
@pytest.mark.django_db
class TestListComments:
    def test_anonymous_can_list(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "cmt_list@example.com")
        fr_id = _submit_fr(api_client, access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        api_client.post(f"/v1/feature-requests/{fr_id}/comments", {"body": "one"}, format="json")
        api_client.post(f"/v1/feature-requests/{fr_id}/comments", {"body": "two"}, format="json")
        api_client.credentials()
        r = api_client.get(f"/v1/feature-requests/{fr_id}/comments")
        assert r.status_code == 200
        assert r.data["total"] == 2
        assert r.data["items"][0]["body"] == "one"


@pytest.mark.e2e
@pytest.mark.django_db
class TestEditComment:
    def test_author_can_edit(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "cmt_edit@example.com")
        fr_id = _submit_fr(api_client, access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "original"}, format="json"
        )
        r = api_client.patch(
            f"/v1/comments/{created.data['id']}", {"body": "revised"}, format="json"
        )
        assert r.status_code == 200
        assert r.data["body"] == "revised"

    def test_non_author_gets_403(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "cmt_edit_a@example.com")
        other_access = _register_and_authenticate(api_client, "cmt_edit_b@example.com")
        fr_id = _submit_fr(api_client, author_access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "mine"}, format="json"
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_access}")
        r = api_client.patch(
            f"/v1/comments/{created.data['id']}", {"body": "hijack"}, format="json"
        )
        assert r.status_code == 403


@pytest.mark.e2e
@pytest.mark.django_db
class TestDeleteComment:
    def test_author_can_delete(self, api_client) -> None:
        access = _register_and_authenticate(api_client, "cmt_del@example.com")
        fr_id = _submit_fr(api_client, access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "bye"}, format="json"
        )
        r = api_client.delete(f"/v1/comments/{created.data['id']}")
        assert r.status_code == 204

        # Body now shows tombstone
        listed = api_client.get(f"/v1/feature-requests/{fr_id}/comments")
        assert listed.data["items"][0]["body"] == "[deleted]"

    def test_moderator_can_delete_others(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "cmt_del_a@example.com")
        mod_access = _register_and_authenticate(
            api_client, "cmt_del_m@example.com", role="moderator"
        )
        fr_id = _submit_fr(api_client, author_access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "bad"}, format="json"
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        r = api_client.delete(f"/v1/comments/{created.data['id']}")
        assert r.status_code == 204


@pytest.mark.e2e
@pytest.mark.django_db
class TestModeratorHide:
    def test_moderator_can_hide(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "cmt_hide_a@example.com")
        mod_access = _register_and_authenticate(
            api_client, "cmt_hide_m@example.com", role="moderator"
        )
        fr_id = _submit_fr(api_client, author_access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "offensive"}, format="json"
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        r = api_client.post(f"/v1/comments/{created.data['id']}/hide")
        assert r.status_code == 200
        assert r.data["body"] == "[hidden by a moderator]"

    def test_regular_user_cannot_hide(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "cmt_hide_u@example.com")
        fr_id = _submit_fr(api_client, author_access)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        created = api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "x"}, format="json"
        )
        r = api_client.post(f"/v1/comments/{created.data['id']}/hide")
        assert r.status_code == 403


@pytest.mark.e2e
@pytest.mark.django_db
class TestTimeline:
    def test_timeline_merges_comments_and_status_logs(self, api_client) -> None:
        author_access = _register_and_authenticate(api_client, "tl_author@example.com")
        mod_access = _register_and_authenticate(api_client, "tl_mod@example.com", role="moderator")
        fr_id = _submit_fr(api_client, author_access)

        # Post a comment
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "comment A"}, format="json"
        )

        # Transition status
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {mod_access}")
        api_client.patch(
            f"/v1/feature-requests/{fr_id}/status",
            {"expected_from": "open", "to_status": "under_review"},
            format="json",
        )

        # Post another comment
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_access}")
        api_client.post(
            f"/v1/feature-requests/{fr_id}/comments", {"body": "comment B"}, format="json"
        )
        api_client.credentials()

        r = api_client.get(f"/v1/feature-requests/{fr_id}/timeline")
        assert r.status_code == 200
        assert r.data["total"] == 3  # 2 comments + 1 status change
        types = [e["type"] for e in r.data["items"]]
        assert "comment" in types
        assert "status_change" in types
