"""Thin DRF views. Translate HTTP <-> domain via serializers and use cases."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..application import (
    confirm_password_reset,
    get_user,
    login,
    logout,
    refresh,
    register_user,
    request_password_reset,
    verify_email,
)
from ..domain import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidEmail,
    TokenExpired,
    TokenInvalid,
    TokenReused,
    WeakPassword,
)
from ..infrastructure.container import build_services
from .serializers import (
    ConfirmPasswordResetIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    RequestPasswordResetIn,
    TokenPairOut,
    UserOut,
    VerifyEmailIn,
)
from .throttling import (
    EmailVerificationThrottle,
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
)


def _bad_request(detail: str, code: str) -> Response:
    return Response({"detail": detail, "code": code}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request: Request) -> Response:
        body = RegisterIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            user = register_user(build_services(), **body.validated_data)
        except (InvalidEmail, WeakPassword) as exc:
            return _bad_request(str(exc), "invalid_input")
        except EmailAlreadyRegistered:
            return Response(
                {"detail": "Email already registered", "code": "email_taken"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(UserOut(user).data, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [EmailVerificationThrottle]

    def post(self, request: Request) -> Response:
        body = VerifyEmailIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            user = verify_email(build_services(), token=body.validated_data["token"])
        except TokenInvalid:
            return Response(
                {"detail": "Token invalid or already used", "code": "token_invalid"},
                status=status.HTTP_410_GONE,
            )
        return Response(UserOut(user).data, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request) -> Response:
        body = LoginIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            _, pair = login(build_services(), **body.validated_data)
        except InvalidCredentials:
            return Response(
                {"detail": "Invalid email or password", "code": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(TokenPairOut({"access": pair.access, "refresh": pair.refresh}).data)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        body = RefreshIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            pair = refresh(build_services(), presented_token=body.validated_data["refresh"])
        except TokenReused:
            return Response(
                {"detail": "Token reuse detected; sessions invalidated", "code": "token_reused"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except (TokenInvalid, TokenExpired):
            return Response(
                {"detail": "Refresh token invalid", "code": "token_invalid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(TokenPairOut({"access": pair.access, "refresh": pair.refresh}).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(build_services(), user_id=request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request: Request) -> Response:
        body = RequestPasswordResetIn(data=request.data)
        body.is_valid(raise_exception=True)
        request_password_reset(build_services(), email=body.validated_data["email"])
        return Response(status=status.HTTP_202_ACCEPTED)


class ConfirmPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        body = ConfirmPasswordResetIn(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            confirm_password_reset(build_services(), **body.validated_data)
        except WeakPassword as exc:
            return _bad_request(str(exc), "invalid_input")
        except TokenInvalid:
            return Response(
                {"detail": "Token invalid or already used", "code": "token_invalid"},
                status=status.HTTP_410_GONE,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = get_user(build_services(), user_id=request.user.id)
        return Response(UserOut(user).data)
