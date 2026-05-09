"""Error classes for the API module."""


class InvalidContainerError(ValueError):
    """Thrown when an invalid container is specified."""


class StorageServiceError(RuntimeError):
    """Thrown for storage URL generation errors."""


__all__ = [
    "InvalidContainerError",
    "StorageServiceError",
]
