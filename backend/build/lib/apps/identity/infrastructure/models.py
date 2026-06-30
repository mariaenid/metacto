"""Django ORM tables for the identity context. Repositories map to domain entities."""
from __future__ import annotations

from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from ..domain import Role


class UserManager(BaseUserManager["UserRecord"]):
    use_in_migrations = True

    def create_user(
        self, email: str, password_hash: str, display_name: str = ""
    ) -> "UserRecord":
        user = self.model(
            email=self.normalize_email(email).lower(),
            display_name=display_name,
            password=password_hash,
        )
        user.save(using=self._db)
        return user


class UserRecord(AbstractBaseUser):
    """Stored row for a domain `User`. Column `password` holds the Argon2id digest."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    display_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=16,
        choices=[(r.value, r.value) for r in Role],
        default=Role.USER.value,
    )
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "identity_user"
        verbose_name = "user"


class RefreshTokenRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        "identity.UserRecord", on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    family_id = models.UUIDField(db_index=True)
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_refresh_token"
        indexes = [
            models.Index(
                fields=["user", "used_at"],
                name="idx_refresh_user_active",
                condition=models.Q(used_at__isnull=True),
            ),
        ]


class EmailVerificationTokenRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        "identity.UserRecord", on_delete=models.CASCADE, related_name="email_tokens"
    )
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_email_verification_token"


class PasswordResetTokenRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        "identity.UserRecord", on_delete=models.CASCADE, related_name="reset_tokens"
    )
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_password_reset_token"
