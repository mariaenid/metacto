"""Identity use cases. Orchestrate domain + ports; no Django or DB imports here."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..domain import (
    Email,
    EmailAlreadyRegistered,
    EmailNotVerified,
    InvalidCredentials,
    Password,
    RefreshToken,
    SingleUseToken,
    TokenExpired,
    TokenInvalid,
    TokenReused,
    User,
)
from .ports import (
    AccessTokenIssuer,
    EmailSender,
    PasswordHasher,
    RefreshTokenRepository,
    SingleUseTokenRepository,
    TokenGenerator,
    UserRepository,
)


@dataclass(slots=True)
class TokenPair:
    access: str
    refresh: str


@dataclass(slots=True)
class IdentityServices:
    users: UserRepository
    refresh_tokens: RefreshTokenRepository
    email_tokens: SingleUseTokenRepository  # kind = "email_verification"
    reset_tokens: SingleUseTokenRepository  # kind = "password_reset"
    hasher: PasswordHasher
    token_generator: TokenGenerator
    access_issuer: AccessTokenIssuer
    email_sender: EmailSender


def register_user(
    services: IdentityServices, *, email: str, display_name: str, password: str
) -> User:
    parsed_email = Email(email)
    parsed_password = Password(password)
    if services.users.get_by_email(parsed_email.value) is not None:
        raise EmailAlreadyRegistered(parsed_email.value)
    user = User.register(
        email=parsed_email,
        display_name=display_name,
        password_hash=services.hasher.hash(parsed_password.value),
    )
    services.users.add(user)
    verification = SingleUseToken.for_email_verification(
        user_id=user.id, token=services.token_generator.generate()
    )
    services.email_tokens.add(verification)
    services.email_sender.send_verification(to=user.email.value, token=verification.token)
    return user


def verify_email(services: IdentityServices, *, token: str) -> User:
    consumed = services.email_tokens.consume(token)
    if consumed is None:
        raise TokenInvalid()
    user = services.users.get_by_id(consumed.user_id)
    if user is None:
        raise TokenInvalid()
    user.mark_email_verified()
    services.users.save(user)
    return user


def login(services: IdentityServices, *, email: str, password: str) -> tuple[User, TokenPair]:
    parsed_email = Email(email)
    user = services.users.get_by_email(parsed_email.value)
    if user is None or not services.hasher.verify(password, user.password_hash):
        raise InvalidCredentials()
    user.record_login()
    services.users.save(user)
    return user, _issue_pair(services, user)


def refresh(services: IdentityServices, *, presented_token: str) -> TokenPair:
    existing = services.refresh_tokens.get_by_token(presented_token)
    if existing is None:
        raise TokenInvalid()
    if existing.used_at is not None:
        services.refresh_tokens.invalidate_family(existing.family_id)
        raise TokenReused()
    if not existing.is_active():
        raise TokenExpired()
    user = services.users.get_by_id(existing.user_id)
    if user is None:
        raise TokenInvalid()
    new = RefreshToken.issue(
        user_id=user.id,
        token=services.token_generator.generate(),
        family_id=existing.family_id,
    )
    services.refresh_tokens.rotate(existing, new)
    return TokenPair(access=services.access_issuer.issue(user), refresh=new.token)


def logout(services: IdentityServices, *, user_id: UUID) -> None:
    services.refresh_tokens.invalidate_all_for_user(user_id)


def request_password_reset(services: IdentityServices, *, email: str) -> None:
    parsed_email = Email(email)
    user = services.users.get_by_email(parsed_email.value)
    if user is None:
        return  # silent: never reveal whether an email is registered
    reset = SingleUseToken.for_password_reset(
        user_id=user.id, token=services.token_generator.generate()
    )
    services.reset_tokens.add(reset)
    services.email_sender.send_password_reset(to=user.email.value, token=reset.token)


def confirm_password_reset(services: IdentityServices, *, token: str, new_password: str) -> None:
    parsed_password = Password(new_password)
    consumed = services.reset_tokens.consume(token)
    if consumed is None:
        raise TokenInvalid()
    user = services.users.get_by_id(consumed.user_id)
    if user is None:
        raise TokenInvalid()
    user.password_hash = services.hasher.hash(parsed_password.value)
    services.users.save(user)
    services.refresh_tokens.invalidate_all_for_user(user.id)


def get_user(services: IdentityServices, *, user_id: UUID) -> User:
    from ..domain import UserNotFound

    user = services.users.get_by_id(user_id)
    if user is None:
        raise UserNotFound(str(user_id))
    return user


def require_verified(user: User) -> None:
    if not user.can_write():
        raise EmailNotVerified(user.email.value)


def _issue_pair(services: IdentityServices, user: User) -> TokenPair:
    refresh_token = RefreshToken.issue(user_id=user.id, token=services.token_generator.generate())
    services.refresh_tokens.add(refresh_token)
    return TokenPair(access=services.access_issuer.issue(user), refresh=refresh_token.token)
