"""Auth endpoints for the identity context (ADR-04)."""

from django.urls import path

from .views import (
    ConfirmPasswordResetView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    RequestPasswordResetView,
    VerifyEmailView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path(
        "auth/password-reset/request",
        RequestPasswordResetView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "auth/password-reset/confirm",
        ConfirmPasswordResetView.as_view(),
        name="auth-password-reset-confirm",
    ),
]
