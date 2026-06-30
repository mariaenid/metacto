"""Comment domain value objects."""

from __future__ import annotations

from dataclasses import dataclass

MAX_BODY_LENGTH = 5000
MIN_BODY_LENGTH = 1


class InvalidBody(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Body:
    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if len(stripped) < MIN_BODY_LENGTH:
            raise InvalidBody("Comment body cannot be empty.")
        if len(stripped) > MAX_BODY_LENGTH:
            raise InvalidBody(f"Comment body cannot exceed {MAX_BODY_LENGTH} characters.")
        object.__setattr__(self, "value", stripped)
