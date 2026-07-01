"""Domain exceptions for the identity context."""


class IdentityError(Exception):
    """Base for all identity domain errors."""


class EmailAlreadyRegistered(IdentityError):
    pass


class InvalidCredentials(IdentityError):
    pass


class EmailNotVerified(IdentityError):
    pass


class TokenInvalid(IdentityError):
    pass


class TokenReused(IdentityError):
    """Raised when a refresh token already marked used is presented again."""


class TokenExpired(IdentityError):
    pass


class UserNotFound(IdentityError):
    pass
