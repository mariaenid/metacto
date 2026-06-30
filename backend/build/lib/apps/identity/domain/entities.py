"""Pure domain entities for the identity context."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from .value_objects import Email, Role

REFRESH_LIFETIME = timedelta(days=30)
EMAIL_VERIFICATION_LIFETIME = timedelta(hours=24)
PASSWORD_RESET_LIFETIME = timedelta(hours=1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class User:
    id: UUID
    email: Email
    display_name: str
    password_hash: str
    role: Role = Role.USER
    email_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    @classmethod
    def register(
        cls, *, email: Email, display_name: str, password_hash: str
    ) -> "User":
        return cls(
            id=uuid4(),
            email=email,
            display_name=display_name.strip(),
            password_hash=password_hash,
        )

    def mark_email_verified(self) -> None:
        self.email_verified = True

    def record_login(self) -> None:
        self.last_login_at = _now()

    def can_write(self) -> bool:
        # Verified email is the gate for submit/vote/comment (RULE-11).
        return self.email_verified

    def can_moderate(self) -> bool:
        return self.role in (Role.MODERATOR, Role.ADMIN)


@dataclass(slots=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    family_id: UUID
    token: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    @classmethod
    def issue(cls, *, user_id: UUID, token: str, family_id: UUID | None = None) -> "RefreshToken":
        return cls(
            id=uuid4(),
            user_id=user_id,
            family_id=family_id or uuid4(),
            token=token,
            expires_at=_now() + REFRESH_LIFETIME,
        )

    def is_active(self) -> bool:
        return self.used_at is None and self.expires_at > _now()

    def mark_used(self) -> None:
        self.used_at = _now()


@dataclass(slots=True)
class SingleUseToken:
    """Shared shape for email verification and password reset tokens."""

    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    @classmethod
    def for_email_verification(cls, *, user_id: UUID, token: str) -> "SingleUseToken":
        return cls(
            id=uuid4(),
            user_id=user_id,
            token=token,
            expires_at=_now() + EMAIL_VERIFICATION_LIFETIME,
        )

    @classmethod
    def for_password_reset(cls, *, user_id: UUID, token: str) -> "SingleUseToken":
        return cls(
            id=uuid4(),
            user_id=user_id,
            token=token,
            expires_at=_now() + PASSWORD_RESET_LIFETIME,
        )

    def is_usable(self) -> bool:
        return self.used_at is None and self.expires_at > _now()
