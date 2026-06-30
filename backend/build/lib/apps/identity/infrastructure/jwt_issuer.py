"""Issues short-lived access JWTs via SimpleJWT (configuration in settings.SIMPLE_JWT)."""
from __future__ import annotations

from rest_framework_simplejwt.tokens import AccessToken

from ..domain import User


class SimpleJWTAccessIssuer:
    def issue(self, user: User) -> str:
        token = AccessToken()
        token["user_id"] = str(user.id)
        token["role"] = user.role.value
        token["email_verified"] = user.email_verified
        return str(token)
