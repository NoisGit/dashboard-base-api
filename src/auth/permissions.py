"""Middleware of role verification to control access based on user roles."""

from typing import List, Tuple

from fastapi import Depends, HTTPException, status

from src.core.enums import UserRole
from src.auth.utils import get_user_data_from_token


class RoleChecker:
    """Middleware to verify user roles for access control."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        user_data: Tuple[int, UserRole] = Depends(get_user_data_from_token),
    ) -> int:
        """Verify if the current user's role is in the allowed roles."""
        user_id, role = user_data

        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        # Return user_id (first element of the tuple)
        return int(user_id)


__all__ = ["RoleChecker"]
