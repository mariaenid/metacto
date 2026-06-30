"""Domain exceptions for the feature_requests context."""


class FeatureRequestError(Exception):
    """Base class."""


class FeatureRequestNotFound(FeatureRequestError):
    pass


class InvalidSortOption(FeatureRequestError):
    pass
