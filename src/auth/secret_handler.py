"""
Secret token utilities for the Coredeck API.

This module provides secure token generation used for authenticated access
flows that require URL-safe, non-guessable tokens.
"""

import secrets


def create_secret_token_urlsafe() -> str:
    """Generate a random URL-safe secret token"""
    return secrets.token_urlsafe(32)
