"""API error module providing error classes for the application."""

from .error import (
    InvalidContainerError,
    StorageServiceError
)

__all__ = [
    "InvalidContainerError",
    "StorageServiceError",
]
