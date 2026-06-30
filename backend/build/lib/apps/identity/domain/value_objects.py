"""Value objects for the identity context. Pure Python, no Django."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


class Role(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalised = self.value.strip().lower()
        if not EMAIL_RE.match(normalised):
            raise InvalidEmail(self.value)
        object.__setattr__(self, "value", normalised)


@dataclass(frozen=True, slots=True)
class Password:
    """Wraps a raw password. Cleared from memory by the hasher after use."""

    value: str

    def __post_init__(self) -> None:
        n = len(self.value)
        if n < MIN_PASSWORD_LENGTH or n > MAX_PASSWORD_LENGTH:
            raise WeakPassword(
                f"password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters"
            )
        if self.value.isspace() or " " * 3 in self.value:
            raise WeakPassword("password contains too much whitespace")


class InvalidEmail(ValueError):
    pass


class WeakPassword(ValueError):
    pass
