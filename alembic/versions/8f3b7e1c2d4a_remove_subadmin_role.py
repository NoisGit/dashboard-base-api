"""Remove the obsolete SUBADMIN database role.

Revision ID: 8f3b7e1c2d4a
Revises: 34de07822d8c
Create Date: 2026-06-11 15:05:35.630038

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8f3b7e1c2d4a'
down_revision: Union[str, Sequence[str], None] = '34de07822d8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove SUBADMIN without silently changing existing accounts."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM users
                WHERE role::text = 'SUBADMIN'
            ) THEN
                RAISE EXCEPTION
                    'Cannot remove SUBADMIN while users still have that role';
            END IF;
        END
        $$;
        """
    )
    op.execute("ALTER TYPE userrole RENAME TO userrole_legacy")
    op.execute(
        "CREATE TYPE userrole AS ENUM "
        "('SUPERADMIN', 'ADMIN', 'OPERATOR', 'CLIENT')"
    )
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole
        USING role::text::userrole
        """
    )
    op.execute("DROP TYPE userrole_legacy")


def downgrade() -> None:
    """Restore the legacy enum value without assigning it to any user."""
    op.execute("ALTER TYPE userrole RENAME TO userrole_current")
    op.execute(
        "CREATE TYPE userrole AS ENUM "
        "('SUPERADMIN', 'ADMIN', 'SUBADMIN', 'OPERATOR', 'CLIENT')"
    )
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole
        USING role::text::userrole
        """
    )
    op.execute("DROP TYPE userrole_current")
