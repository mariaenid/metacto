"""Concrete repositories. Map between ORM rows and domain entities."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from django.db import transaction

from ..domain import Email, RefreshToken, Role, SingleUseToken, TokenReused, User
from .models import (
    EmailVerificationTokenRecord,
    PasswordResetTokenRecord,
    RefreshTokenRecord,
    UserRecord,
)


def _user_from_record(row: UserRecord) -> User:
    return User(
        id=row.id,
        email=Email(row.email),
        display_name=row.display_name,
        password_hash=row.password,
        role=Role(row.role),
        email_verified=row.email_verified,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
    )


def _refresh_from_record(row: RefreshTokenRecord) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        family_id=row.family_id,
        token=row.token,
        expires_at=row.expires_at,
        used_at=row.used_at,
        created_at=row.created_at,
    )


def _single_use_from_record(
    row: EmailVerificationTokenRecord | PasswordResetTokenRecord,
) -> SingleUseToken:
    return SingleUseToken(
        id=row.id,
        user_id=row.user_id,
        token=row.token,
        expires_at=row.expires_at,
        used_at=row.used_at,
        created_at=row.created_at,
    )


class DjangoUserRepository:
    def add(self, user: User) -> None:
        UserRecord.objects.create(
            id=user.id,
            email=user.email.value,
            display_name=user.display_name,
            password=user.password_hash,
            role=user.role.value,
            email_verified=user.email_verified,
            last_login_at=user.last_login_at,
        )

    def get_by_id(self, user_id: UUID) -> User | None:
        row = UserRecord.objects.filter(id=user_id).first()
        return _user_from_record(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = UserRecord.objects.filter(email=email.lower()).first()
        return _user_from_record(row) if row else None

    def save(self, user: User) -> None:
        UserRecord.objects.filter(id=user.id).update(
            email=user.email.value,
            display_name=user.display_name,
            password=user.password_hash,
            role=user.role.value,
            email_verified=user.email_verified,
            last_login_at=user.last_login_at,
        )


class DjangoRefreshTokenRepository:
    def add(self, token: RefreshToken) -> None:
        RefreshTokenRecord.objects.create(
            id=token.id,
            user_id=token.user_id,
            family_id=token.family_id,
            token=token.token,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )

    def get_by_token(self, token: str) -> RefreshToken | None:
        row = RefreshTokenRecord.objects.filter(token=token).first()
        return _refresh_from_record(row) if row else None

    def rotate(self, old: RefreshToken, new: RefreshToken) -> None:
        with transaction.atomic():
            now = datetime.now(timezone.utc)
            # Compare-and-set: only mark used if it wasn't already. If we lose the race,
            # another rotation already used this token -> treat as reuse and invalidate the family.
            updated = RefreshTokenRecord.objects.filter(
                token=old.token, used_at__isnull=True
            ).update(used_at=now)
            if updated == 0:
                self.invalidate_family(old.family_id)
                raise TokenReused()
            RefreshTokenRecord.objects.create(
                id=new.id,
                user_id=new.user_id,
                family_id=new.family_id,
                token=new.token,
                expires_at=new.expires_at,
            )

    def invalidate_family(self, family_id: UUID) -> None:
        RefreshTokenRecord.objects.filter(
            family_id=family_id, used_at__isnull=True
        ).update(used_at=datetime.now(timezone.utc))

    def invalidate_all_for_user(self, user_id: UUID) -> None:
        RefreshTokenRecord.objects.filter(
            user_id=user_id, used_at__isnull=True
        ).update(used_at=datetime.now(timezone.utc))


class DjangoEmailVerificationRepository:
    kind = "email_verification"

    def add(self, token: SingleUseToken) -> None:
        EmailVerificationTokenRecord.objects.create(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )

    def consume(self, token: str) -> SingleUseToken | None:
        now = datetime.now(timezone.utc)
        with transaction.atomic():
            updated = EmailVerificationTokenRecord.objects.filter(
                token=token, used_at__isnull=True, expires_at__gt=now
            ).update(used_at=now)
            if updated == 0:
                return None
            row = EmailVerificationTokenRecord.objects.get(token=token)
            return _single_use_from_record(row)


class DjangoPasswordResetRepository:
    kind = "password_reset"

    def add(self, token: SingleUseToken) -> None:
        PasswordResetTokenRecord.objects.create(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )

    def consume(self, token: str) -> SingleUseToken | None:
        now = datetime.now(timezone.utc)
        with transaction.atomic():
            updated = PasswordResetTokenRecord.objects.filter(
                token=token, used_at__isnull=True, expires_at__gt=now
            ).update(used_at=now)
            if updated == 0:
                return None
            row = PasswordResetTokenRecord.objects.get(token=token)
            return _single_use_from_record(row)
