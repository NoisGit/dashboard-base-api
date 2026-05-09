"""
Config package for the Coredeck API.

This package centralizes application configuration and related utilities.
It exposes the main Settings object and helper functions used across the project.
"""

from .config import Settings, settings

__all__ = [
    "Settings",
    "settings",
]
