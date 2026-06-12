"""Add company subscriptions, plans, trials and billing events.

Revision ID: c2a4f6e8b901
Revises: 8f3b7e1c2d4a
Create Date: 2026-06-11 15:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql


revision: str = "c2a4f6e8b901"
down_revision: Union[str, Sequence[str], None] = "8f3b7e1c2d4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the company-owned commercial subscription layer."""
    op.add_column(
        "plans",
        sa.Column("code", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    )
    op.add_column(
        "plans",
        sa.Column(
            "description",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "plans",
        sa.Column(
            "monthly_price_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "plans",
        sa.Column(
            "qty_storage_bytes",
            sa.BigInteger(),
            nullable=False,
            server_default=str(1024 * 1024 * 1024),
        ),
    )
    op.add_column(
        "plans",
        sa.Column(
            "stripe_price_id",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "plans",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.execute("UPDATE plans SET code = 'legacy-' || id::text WHERE code IS NULL")
    op.alter_column("plans", "code", nullable=False)
    op.create_index(op.f("ix_plans_code"), "plans", ["code"], unique=True)

    op.execute(
        """
        INSERT INTO plans (
            code, name, description, monthly_price_cents,
            qty_locations, qty_admins, qty_operators, qty_daily_reads,
            qty_storage_bytes, is_active
        ) VALUES
            (
                'starter', 'Starter', 'Para operaciones pequeñas', 2900,
                2, 2, 10, 500, 1073741824, true
            ),
            (
                'growth', 'Growth', 'Para empresas en crecimiento', 7900,
                10, 5, 50, 5000, 10737418240, true
            ),
            (
                'scale', 'Scale', 'Para operaciones multi-sede', 14900,
                50, 20, 250, 50000, 107374182400, true
            )
        ON CONFLICT (code) DO NOTHING
        """
    )

    subscription_status = postgresql.ENUM(
        "TRIALING",
        "ACTIVE",
        "PAST_DUE",
        "CANCELED",
        name="subscriptionstatus",
        create_type=False,
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "company_subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", subscription_status, nullable=False),
        sa.Column("trial_started_at", sa.DateTime(), nullable=False),
        sa.Column("trial_ends_at", sa.DateTime(), nullable=False),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column(
            "provider",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
        ),
        sa.Column(
            "provider_customer_id",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=True,
        ),
        sa.Column(
            "provider_subscription_id",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=True,
        ),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            name="uq_company_subscription_company",
        ),
        sa.UniqueConstraint("provider_subscription_id"),
    )
    op.create_index(
        op.f("ix_company_subscription_company_id"),
        "company_subscription",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_subscription_plan_id"),
        "company_subscription",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_subscription_provider_customer_id"),
        "company_subscription",
        ["provider_customer_id"],
        unique=False,
    )

    op.create_table(
        "billing_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
        ),
        sa.Column(
            "provider_event_id",
            sqlmodel.sql.sqltypes.AutoString(length=120),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sqlmodel.sql.sqltypes.AutoString(length=120),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_billing_event_provider_event_id"),
        "billing_event",
        ["provider_event_id"],
        unique=True,
    )

    op.execute(
        """
        INSERT INTO company_subscription (
            company_id, plan_id, status, trial_started_at, trial_ends_at,
            provider, created_at, updated_at
        )
        SELECT
            company.id,
            plans.id,
            'TRIALING'::subscriptionstatus,
            now(),
            now() + interval '14 days',
            'stripe',
            now(),
            now()
        FROM company
        JOIN plans ON plans.code = 'growth'
        WHERE company.parent_company_id IS NULL
        ON CONFLICT (company_id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove the company subscription layer."""
    op.drop_index(
        op.f("ix_billing_event_provider_event_id"),
        table_name="billing_event",
    )
    op.drop_table("billing_event")
    op.drop_index(
        op.f("ix_company_subscription_provider_customer_id"),
        table_name="company_subscription",
    )
    op.drop_index(
        op.f("ix_company_subscription_plan_id"),
        table_name="company_subscription",
    )
    op.drop_index(
        op.f("ix_company_subscription_company_id"),
        table_name="company_subscription",
    )
    op.drop_table("company_subscription")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")

    op.drop_index(op.f("ix_plans_code"), table_name="plans")
    op.drop_column("plans", "is_active")
    op.drop_column("plans", "stripe_price_id")
    op.drop_column("plans", "qty_storage_bytes")
    op.drop_column("plans", "monthly_price_cents")
    op.drop_column("plans", "description")
    op.drop_column("plans", "code")
