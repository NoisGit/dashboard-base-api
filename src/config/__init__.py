"""
Config package for the Sentinel Enterprise API.

This package centralizes application configuration and related utilities.
It exposes the main Settings object and helper functions used across the project.
"""

from .config import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
