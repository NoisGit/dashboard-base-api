
"""
Plan database model for the Coredeck API.

Represents the subscription/usage plan assigned to users, including limits
for workspaces, admins, operators and daily reads.
"""

from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class Plan(SQLModel, table=True):
    """
    Subscription plan entity.

    Matches the `plan` table in the ERD:

    - id
    - name
    - qty_locations
    - qty_admins
    - qty_operators
    - qty_daily_reads
    """

    __tablename__ = "plans"

    id: Optional[int] = Field(default=None, primary_key=True)

    # DBML: name varchar(100)
    name: str = Field(max_length=100)

    # DBML: qty_locations int, qty_admins int, qty_operators int, qty_daily_reads int
    qty_locations: int
    qty_admins: int
    qty_operators: int
    qty_daily_reads: int

    # Relationships
    users: List["User"] = Relationship(back_populates="plan")
