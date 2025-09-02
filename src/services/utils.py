class ServiceError(Exception):
    """Base class for service errors."""


class NotFound(ServiceError):
    """Requested resource was not found."""


class Conflict(ServiceError):
    """Uniqueness or state conflict."""


class Ambiguous(ServiceError):
    """More than one matching resource found where one was expected."""
