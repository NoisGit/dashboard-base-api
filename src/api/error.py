"""Error classes for the API module."""


class InvalidContainerError(ValueError):
    """Thrown when an invalid container is specified."""


class StorageServiceError(RuntimeError):
    """Thrown for storage URL generation errors."""


# Backward-compatible alias while legacy imports migrate to StorageServiceError.
AzureServiceError = StorageServiceError


__all__ = [
    "InvalidContainerError",
    "StorageServiceError",
    "AzureServiceError",
]
