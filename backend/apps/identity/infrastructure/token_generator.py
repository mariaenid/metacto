"""Cryptographically random opaque tokens (refresh, verify, reset)."""

from __future__ import annotations

import secrets


class SecretsTokenGenerator:
    def generate(self) -> str:
        # 32 bytes → 43-char base64url string; ample entropy for refresh and single-use tokens.
        return secrets.token_urlsafe(32)
