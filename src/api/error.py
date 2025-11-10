"""Error classes for the API module."""


class InvalidContainerError(ValueError):
    """Thrown when an invalid container is specified."""


class AzureServiceError(RuntimeError):
    """Thrown for general errors when generating the URL."""


__all__ = [
    "InvalidContainerError",
    "AzureServiceError"
]
