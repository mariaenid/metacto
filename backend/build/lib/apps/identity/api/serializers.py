"""DRF serializers for the identity API. Pure data shape; logic lives in use cases."""
from __future__ import annotations

from rest_framework import serializers


class RegisterIn(serializers.Serializer):
    email = serializers.EmailField()
    display_name = serializers.CharField(min_length=1, max_length=150)
    password = serializers.CharField(write_only=True)


class LoginIn(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenPairOut(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshIn(serializers.Serializer):
    refresh = serializers.CharField()


class VerifyEmailIn(serializers.Serializer):
    token = serializers.CharField()


class RequestPasswordResetIn(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmPasswordResetIn(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


class UserOut(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    role = serializers.SerializerMethodField()
    email_verified = serializers.BooleanField()

    def get_email(self, obj) -> str:
        return obj.email.value

    def get_role(self, obj) -> str:
        return obj.role.value
