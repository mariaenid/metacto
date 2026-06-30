"""Permission classes enforcing identity-related gates."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """Write endpoints reject users with `email_verified = False` (RULE-11)."""

    message = "Email must be verified before performing this action."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "email_verified", False))


class IsModerator(BasePermission):
    """Status-transition endpoints require moderator or admin role."""

    message = "Moderator or admin role required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        return getattr(user, "role", "") in ("moderator", "admin")


class IsAdmin(BasePermission):
    """Admin-only endpoints (stats, user management)."""

    message = "Admin role required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "role", "") == "admin")
