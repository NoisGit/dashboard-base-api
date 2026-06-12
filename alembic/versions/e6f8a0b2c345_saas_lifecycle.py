"""saas lifecycle

Revision ID: e6f8a0b2c345
Revises: d4b6c8e0f123
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e6f8a0b2c345"
down_revision: Union[str, None] = "d4b6c8e0f123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    invitation_status = postgresql.ENUM(
        "PENDING",
        "ACCEPTED",
        "REVOKED",
        "EXPIRED",
        name="invitationstatus",
        create_type=False,
    )
    invitation_status_ddl = postgresql.ENUM(
        "PENDING",
        "ACCEPTED",
        "REVOKED",
        "EXPIRED",
        name="invitationstatus",
    )
    invitation_status_ddl.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
    op.create_table(
        "tenant_invitation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False
        ),
        sa.Column(
            "location_id", sa.Integer(), sa.ForeignKey("location.id"), nullable=True
        ),
        sa.Column(
            "invited_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "SUPERADMIN",
                "ADMIN",
                "OPERATOR",
                "CLIENT",
                name="userrole",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", invitation_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("resend_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_tenant_invitation_company_id", "tenant_invitation", ["company_id"]
    )
    op.create_index("ix_tenant_invitation_email", "tenant_invitation", ["email"])
    op.create_index(
        "ix_tenant_invitation_token_hash",
        "tenant_invitation",
        ["token_hash"],
        unique=True,
    )
    op.create_table(
        "communication_preference",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False
        ),
        sa.Column("billing_emails", sa.Boolean(), nullable=False),
        sa.Column("product_emails", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("company_id", name="uq_communication_preference_company"),
    )
    op.create_index(
        "ix_communication_preference_company_id",
        "communication_preference",
        ["company_id"],
    )
    op.create_table(
        "email_verification_token",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_email_verification_token_user_id", "email_verification_token", ["user_id"]
    )
    op.create_index(
        "ix_email_verification_token_token_hash",
        "email_verification_token",
        ["token_hash"],
        unique=True,
    )
    op.create_table(
        "email_delivery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(160), nullable=False),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=True
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("recipient", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(180), nullable=False),
        sa.Column("template_name", sa.String(100), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(255), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_email_delivery_event_key", "email_delivery", ["event_key"], unique=True
    )
    op.create_index("ix_email_delivery_company_id", "email_delivery", ["company_id"])
    op.create_index("ix_email_delivery_status", "email_delivery", ["status"])
    op.create_index(
        "ix_email_delivery_scheduled_for", "email_delivery", ["scheduled_for"]
    )
    op.create_table(
        "billing_invoice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id", sa.Integer(), sa.ForeignKey("company.id"), nullable=False
        ),
        sa.Column("provider_invoice_id", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("amount_due", sa.Integer(), nullable=False),
        sa.Column("amount_paid", sa.Integer(), nullable=False),
        sa.Column("hosted_invoice_url", sa.String(500), nullable=True),
        sa.Column("invoice_pdf", sa.String(500), nullable=True),
        sa.Column("period_start", sa.DateTime(), nullable=True),
        sa.Column("period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_billing_invoice_company_id", "billing_invoice", ["company_id"])
    op.create_index(
        "ix_billing_invoice_provider_invoice_id",
        "billing_invoice",
        ["provider_invoice_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("billing_invoice")
    op.drop_table("email_delivery")
    op.drop_table("email_verification_token")
    op.drop_table("communication_preference")
    op.drop_table("tenant_invitation")
    op.drop_column("users", "email_verified_at")
    sa.Enum(name="invitationstatus").drop(op.get_bind(), checkfirst=True)
