"""Ports the application layer depends on. Implementations live in infrastructure/."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ..domain import RefreshToken, SingleUseToken, User


class PasswordHasher(Protocol):
    def hash(self, raw: str) -> str: ...
    def verify(self, raw: str, hashed: str) -> bool: ...


class TokenGenerator(Protocol):
    """Cryptographically random opaque tokens (refresh, verify, reset)."""

    def generate(self) -> str: ...


class AccessTokenIssuer(Protocol):
    """Mints a short-lived JWT for the given user."""

    def issue(self, user: User) -> str: ...


class UserRepository(Protocol):
    def add(self, user: User) -> None: ...
    def get_by_id(self, user_id: UUID) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def save(self, user: User) -> None: ...


class RefreshTokenRepository(Protocol):
    def add(self, token: RefreshToken) -> None: ...
    def get_by_token(self, token: str) -> RefreshToken | None: ...
    def rotate(self, old: RefreshToken, new: RefreshToken) -> None:
        """Atomic: mark `old` used and insert `new` in the same transaction."""

    def invalidate_family(self, family_id: UUID) -> None: ...
    def invalidate_all_for_user(self, user_id: UUID) -> None: ...


class SingleUseTokenRepository(Protocol):
    """Used for both email verification and password reset tokens."""

    kind: str

    def add(self, token: SingleUseToken) -> None: ...
    def consume(self, token: str) -> SingleUseToken | None:
        """Atomic: returns the row only if marking it used succeeded."""


class EmailSender(Protocol):
    def send_verification(self, *, to: str, token: str) -> None: ...
    def send_password_reset(self, *, to: str, token: str) -> None: ...
