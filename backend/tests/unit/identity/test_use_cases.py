"""Use-case orchestration tested against in-memory fakes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from uuid import UUID

import pytest

from apps.identity.application import (
    IdentityServices,
    confirm_password_reset,
    login,
    logout,
    refresh,
    register_user,
    request_password_reset,
    verify_email,
)
from apps.identity.domain import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    RefreshToken,
    SingleUseToken,
    TokenInvalid,
    TokenReused,
    User,
)


@dataclass(slots=True)
class _UserRepo:
    by_id: dict[UUID, User] = field(default_factory=dict)
    by_email: dict[str, User] = field(default_factory=dict)

    def add(self, u: User) -> None:
        self.by_id[u.id] = u
        self.by_email[u.email.value] = u

    def get_by_id(self, uid: UUID) -> User | None:
        return self.by_id.get(uid)

    def get_by_email(self, email: str) -> User | None:
        return self.by_email.get(email.lower())

    def save(self, u: User) -> None:
        self.by_id[u.id] = u
        self.by_email[u.email.value] = u


@dataclass(slots=True)
class _RefreshRepo:
    by_token: dict[str, RefreshToken] = field(default_factory=dict)

    def add(self, t: RefreshToken) -> None:
        self.by_token[t.token] = t

    def get_by_token(self, token: str) -> RefreshToken | None:
        return self.by_token.get(token)

    def rotate(self, old: RefreshToken, new: RefreshToken) -> None:
        old.mark_used()
        self.by_token[old.token] = old
        self.by_token[new.token] = new

    def invalidate_family(self, family_id: UUID) -> None:
        for t in self.by_token.values():
            if t.family_id == family_id:
                t.mark_used()

    def invalidate_all_for_user(self, user_id: UUID) -> None:
        for t in self.by_token.values():
            if t.user_id == user_id and t.used_at is None:
                t.mark_used()


@dataclass(slots=True)
class _SingleUseRepo:
    kind: str
    by_token: dict[str, SingleUseToken] = field(default_factory=dict)

    def add(self, t: SingleUseToken) -> None:
        self.by_token[t.token] = t

    def consume(self, token: str) -> SingleUseToken | None:
        t = self.by_token.get(token)
        if t is None or not t.is_usable():
            return None
        from datetime import datetime

        t.used_at = datetime.now(UTC)
        return t


@dataclass(slots=True)
class _Hasher:
    def hash(self, raw: str) -> str:
        return f"hash::{raw}"

    def verify(self, raw: str, hashed: str) -> bool:
        return hashed == f"hash::{raw}"


@dataclass(slots=True)
class _TokenGen:
    counter: int = 0

    def generate(self) -> str:
        self.counter += 1
        return f"tok{self.counter}"


@dataclass(slots=True)
class _Issuer:
    def issue(self, user: User) -> str:
        return f"access::{user.id}"


@dataclass(slots=True)
class _EmailSender:
    sent: list[tuple[str, str, str]] = field(default_factory=list)

    def send_verification(self, *, to: str, token: str) -> None:
        self.sent.append(("verify", to, token))

    def send_password_reset(self, *, to: str, token: str) -> None:
        self.sent.append(("reset", to, token))


@pytest.fixture
def services() -> IdentityServices:
    return IdentityServices(
        users=_UserRepo(),
        refresh_tokens=_RefreshRepo(),
        email_tokens=_SingleUseRepo(kind="email_verification"),
        reset_tokens=_SingleUseRepo(kind="password_reset"),
        hasher=_Hasher(),
        token_generator=_TokenGen(),
        access_issuer=_Issuer(),
        email_sender=_EmailSender(),
    )


@pytest.mark.unit
class TestRegister:
    def test_creates_unverified_user_and_sends_token(self, services: IdentityServices) -> None:
        u = register_user(
            services,
            email="maria@example.com",
            display_name="Maria",
            password="CorrectHorseBattery!7",
        )
        assert u.email_verified is False
        assert any(kind == "verify" for kind, *_ in services.email_sender.sent)  # type: ignore[attr-defined]

    def test_duplicate_email_raises(self, services: IdentityServices) -> None:
        register_user(services, email="a@b.com", display_name="X", password="CorrectHorseBattery!7")
        with pytest.raises(EmailAlreadyRegistered):
            register_user(
                services,
                email="A@b.com",
                display_name="Y",
                password="CorrectHorseBattery!7",
            )


@pytest.mark.unit
class TestVerifyEmail:
    def test_consumes_token_and_marks_verified(self, services: IdentityServices) -> None:
        register_user(services, email="a@b.com", display_name="X", password="CorrectHorseBattery!7")
        _, _, token = services.email_sender.sent[0]  # type: ignore[attr-defined]
        u = verify_email(services, token=token)
        assert u.email_verified is True
        with pytest.raises(TokenInvalid):
            verify_email(services, token=token)


@pytest.mark.unit
class TestLogin:
    def test_returns_token_pair_on_success(self, services: IdentityServices) -> None:
        register_user(
            services,
            email="a@b.com",
            display_name="X",
            password="CorrectHorseBattery!7",
        )
        user, pair = login(services, email="a@b.com", password="CorrectHorseBattery!7")
        assert pair.access.startswith("access::")
        assert pair.refresh != ""
        assert user.last_login_at is not None

    def test_wrong_password_raises(self, services: IdentityServices) -> None:
        register_user(
            services,
            email="a@b.com",
            display_name="X",
            password="CorrectHorseBattery!7",
        )
        with pytest.raises(InvalidCredentials):
            login(services, email="a@b.com", password="WrongHorseBattery!9")

    def test_unknown_email_raises(self, services: IdentityServices) -> None:
        with pytest.raises(InvalidCredentials):
            login(services, email="nope@b.com", password="CorrectHorseBattery!7")


@pytest.mark.unit
class TestRefresh:
    def test_rotates_and_invalidates_previous(self, services: IdentityServices) -> None:
        register_user(
            services,
            email="a@b.com",
            display_name="X",
            password="CorrectHorseBattery!7",
        )
        _, first = login(services, email="a@b.com", password="CorrectHorseBattery!7")
        second = refresh(services, presented_token=first.refresh)
        assert second.refresh != first.refresh

    def test_reusing_old_token_triggers_breach(self, services: IdentityServices) -> None:
        register_user(
            services,
            email="a@b.com",
            display_name="X",
            password="CorrectHorseBattery!7",
        )
        _, first = login(services, email="a@b.com", password="CorrectHorseBattery!7")
        refresh(services, presented_token=first.refresh)
        with pytest.raises(TokenReused):
            refresh(services, presented_token=first.refresh)


@pytest.mark.unit
class TestPasswordReset:
    def test_silent_for_unknown_email(self, services: IdentityServices) -> None:
        request_password_reset(services, email="nobody@example.com")
        assert services.email_sender.sent == []  # type: ignore[attr-defined]

    def test_round_trip_changes_password_and_invalidates_refresh(
        self, services: IdentityServices
    ) -> None:
        register_user(
            services,
            email="a@b.com",
            display_name="X",
            password="CorrectHorseBattery!7",
        )
        _, pair = login(services, email="a@b.com", password="CorrectHorseBattery!7")
        request_password_reset(services, email="a@b.com")
        reset_token = next(
            tok
            for kind, _, tok in services.email_sender.sent
            if kind == "reset"  # type: ignore[attr-defined]
        )
        confirm_password_reset(services, token=reset_token, new_password="NewHorseBattery!42")
        with pytest.raises(InvalidCredentials):
            login(services, email="a@b.com", password="CorrectHorseBattery!7")
        login(services, email="a@b.com", password="NewHorseBattery!42")
        with pytest.raises(TokenReused):
            refresh(services, presented_token=pair.refresh)


@pytest.mark.unit
def test_logout_invalidates_all_refresh_tokens(services: IdentityServices) -> None:
    register_user(services, email="a@b.com", display_name="X", password="CorrectHorseBattery!7")
    user, pair = login(services, email="a@b.com", password="CorrectHorseBattery!7")
    logout(services, user_id=user.id)
    with pytest.raises(TokenReused):
        refresh(services, presented_token=pair.refresh)
