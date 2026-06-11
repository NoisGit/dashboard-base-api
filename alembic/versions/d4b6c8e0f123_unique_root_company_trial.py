"""Prevent duplicate trials for one root company identifier.

Revision ID: d4b6c8e0f123
Revises: c2a4f6e8b901
Create Date: 2026-06-11 15:52:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4b6c8e0f123"
down_revision: Union[str, Sequence[str], None] = "c2a4f6e8b901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforce one root tenant per normalized company identifier."""
    op.create_index(
        "uq_root_company_id_number",
        "company",
        ["id_number"],
        unique=True,
        postgresql_where=sa.text(
            "parent_company_id IS NULL AND id_number IS NOT NULL"
        ),
    )


def downgrade() -> None:
    """Remove the root-company identifier uniqueness constraint."""
    op.drop_index("uq_root_company_id_number", table_name="company")
