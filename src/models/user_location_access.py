"""User–Location Access database model for the Locentr API.

Represents the association between a user and a location (site/project),
including who created the link and when it was created.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User
    from .location import Location


class UserLocationAccess(SQLModel, table=True):
    """
    Join table between users and locations.

    A record in this table indicates that a given user has access
    to a specific location. It also keeps track of the creator user
    and the creation timestamp.

    Matches the `user_location_access` table in the ERD:

    - id
    - user_id
    - location_id
    - created_by
    - created_at
    """

    __tablename__ = "user_location_access"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    location_id: int = Field(foreign_key="location.id")

    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(
        back_populates="location_accesses",
        sa_relationship_kwargs={
            "foreign_keys": "[UserLocationAccess.user_id]"},
    )
    location: "Location" = Relationship(back_populates="user_locations")
    creator: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[UserLocationAccess.created_by]"},
    )
