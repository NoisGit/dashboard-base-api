"""Add indexes for operational queries.

Revision ID: f7a9c1d3e5b7
Revises: e6f8a0b2c345
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f7a9c1d3e5b7"
down_revision: Union[str, Sequence[str], None] = "e6f8a0b2c345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_access_log_location_created_at",
        "access_log",
        ["location_id", "created_at"],
    )
    op.create_index(
        "ix_access_log_location_exit_date",
        "access_log",
        ["location_id", "exit_date"],
    )
    op.create_index(
        "ix_access_list_company_type_location",
        "access_list",
        ["company_id", "type_access_list_id", "location_id"],
    )
    op.create_index(
        "ix_tenant_invitation_company_status_expires",
        "tenant_invitation",
        ["company_id", "status", "expires_at"],
    )
    op.create_index(
        "ix_email_delivery_status_scheduled_attempts",
        "email_delivery",
        ["status", "scheduled_for", "attempts"],
    )
    op.create_index(
        "ix_billing_invoice_company_created_at",
        "billing_invoice",
        ["company_id", "created_at"],
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index(
        "ix_audit_log_user_created_at",
        "audit_log",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_user_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index(
        "ix_billing_invoice_company_created_at",
        table_name="billing_invoice",
    )
    op.drop_index(
        "ix_email_delivery_status_scheduled_attempts",
        table_name="email_delivery",
    )
    op.drop_index(
        "ix_tenant_invitation_company_status_expires",
        table_name="tenant_invitation",
    )
    op.drop_index(
        "ix_access_list_company_type_location",
        table_name="access_list",
    )
    op.drop_index(
        "ix_access_log_location_exit_date",
        table_name="access_log",
    )
    op.drop_index(
        "ix_access_log_location_created_at",
        table_name="access_log",
    )
