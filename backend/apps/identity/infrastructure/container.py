"""Wires concrete adapters into the IdentityServices dataclass for the API layer."""

from __future__ import annotations

from ..application import IdentityServices
from .email_sender import ConsoleEmailSender
from .hasher import Argon2idPasswordHasher
from .jwt_issuer import SimpleJWTAccessIssuer
from .repositories import (
    DjangoEmailVerificationRepository,
    DjangoPasswordResetRepository,
    DjangoRefreshTokenRepository,
    DjangoUserRepository,
)
from .token_generator import SecretsTokenGenerator


def build_services() -> IdentityServices:
    return IdentityServices(
        users=DjangoUserRepository(),
        refresh_tokens=DjangoRefreshTokenRepository(),
        email_tokens=DjangoEmailVerificationRepository(),
        reset_tokens=DjangoPasswordResetRepository(),
        hasher=Argon2idPasswordHasher(),
        token_generator=SecretsTokenGenerator(),
        access_issuer=SimpleJWTAccessIssuer(),
        email_sender=ConsoleEmailSender(),
    )
