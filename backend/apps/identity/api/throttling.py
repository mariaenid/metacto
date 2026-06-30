"""Redis-backed fixed-window throttles for auth endpoints (ADR-07)."""

from __future__ import annotations

import re

from rest_framework.throttling import SimpleRateThrottle

_RATE_RE = re.compile(r"^(?P<count>\d+)/(?P<n>\d+)?(?P<unit>s|m|min|h|hour|d|day)$")
_UNIT_SECONDS = {"s": 1, "m": 60, "min": 60, "h": 3600, "hour": 3600, "d": 86400, "day": 86400}


class _CompoundRateThrottle(SimpleRateThrottle):
    """Accepts rates like '5/10min' or '3/hour' in addition to DRF's native shapes."""

    def parse_rate(self, rate: str | None) -> tuple[int | None, int | None]:
        if rate is None:
            return (None, None)
        match = _RATE_RE.match(rate)
        if not match:
            return super().parse_rate(rate)
        count = int(match["count"])
        n = int(match["n"]) if match["n"] else 1
        duration = n * _UNIT_SECONDS[match["unit"]]
        return (count, duration)


class LoginThrottle(_CompoundRateThrottle):
    scope = "auth_login"
    rate = "5/10min"

    def get_cache_key(self, request, view) -> str:
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class RegisterThrottle(_CompoundRateThrottle):
    scope = "auth_register"
    rate = "3/hour"

    def get_cache_key(self, request, view) -> str:
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class PasswordResetThrottle(_CompoundRateThrottle):
    scope = "auth_password_reset"
    rate = "3/day"

    def get_cache_key(self, request, view) -> str | None:
        email = request.data.get("email") if hasattr(request, "data") else None
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email.lower()}


class EmailVerificationThrottle(_CompoundRateThrottle):
    scope = "auth_email_verify"
    rate = "10/hour"

    def get_cache_key(self, request, view) -> str:
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
