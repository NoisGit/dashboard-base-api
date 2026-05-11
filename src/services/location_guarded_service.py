"""Guarded location mutations for Coredeck API."""

from datetime import datetime

from src.schemas import LocationUpdateRequest
from src.services.location_service import LocationService


class LocationGuardedService(LocationService):
    """Location service with guarded mutations."""

    async def update_location(
        self,
        user_id: int,
        location_id: int,
        payload: LocationUpdateRequest,
    ):
        """Update a location."""
        location = await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        update_data = payload.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(location, key, value)

        self.session.add(location)
        await self.session.commit()

    async def soft_delete_location(
        self,
        user_id: int,
        location_id: int,
    ):
        """Soft delete a location."""
        location = await self.check_user_permission_on_location(
            user_id=user_id,
            location_id=location_id,
        )

        location.is_active = False
        self.session.add(location)
        await self.session.commit()


__all__ = ["LocationGuardedService"]
