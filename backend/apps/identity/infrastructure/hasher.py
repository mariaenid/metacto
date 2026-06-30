"""Argon2id adapter for the PasswordHasher port (see ADR-04, RULE-14)."""

from __future__ import annotations

from argon2 import PasswordHasher as Argon2
from argon2.exceptions import InvalidHashError, VerifyMismatchError


class Argon2idPasswordHasher:
    def __init__(self) -> None:
        # m=64MB, t=3, p=4 — see ADR-04. Tunable per deployment.
        self._hasher = Argon2(time_cost=3, memory_cost=64 * 1024, parallelism=4)

    def hash(self, raw: str) -> str:
        return self._hasher.hash(raw)

    def verify(self, raw: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, raw)
        except (VerifyMismatchError, InvalidHashError):
            return False
