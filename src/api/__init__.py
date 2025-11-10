"""API error module providing error classes for the application."""

from .error import (
    InvalidContainerError,
    AzureServiceError
)

__all__ = [
    "InvalidContainerError",
    "AzureServiceError",
]
