"""remove company_id from location

Revision ID: 59401fdb06d4
Revises: 7240d6745044
Create Date: 2026-03-26 12:43:47.995433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59401fdb06d4'
down_revision: Union[str, Sequence[str], None] = 'b9cd0c8a50c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f('location_company_id_fkey'),
        'location',
        type_='foreignkey',
    )
    op.drop_column('location', 'company_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'location',
        sa.Column('company_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f('location_company_id_fkey'),
        'location',
        'company',
        ['company_id'],
        ['id'],
    )
