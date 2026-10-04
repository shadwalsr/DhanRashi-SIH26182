"""create reports and sahyog tables

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-10-03 01:45:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "g7h8i9j0k1l2"
down_revision = "f6g7h8i9j0k1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("pdf_hash", sa.String(length=64), nullable=True),
        sa.Column("pdf_path", sa.Text(), nullable=True),
        sa.Column("data_payload", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approval_comment", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_case_id"), "reports", ["case_id"], unique=False)
    op.create_index(op.f("ix_reports_investigation_id"), "reports", ["investigation_id"], unique=False)

    # 2. Create sahyog_requests table
    op.create_table(
        "sahyog_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=False),
        sa.Column("target_vasp_id", sa.String(length=100), nullable=False),
        sa.Column("target_vasp_name", sa.String(length=255), nullable=False),
        sa.Column("target_wallet_address", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("statutory_basis", sa.String(length=255), nullable=False, server_default="Section 91 CrPC / Section 94 BNSS"),
        sa.Column("officer_name", sa.String(length=255), nullable=False),
        sa.Column("officer_designation", sa.String(length=255), nullable=False, server_default="Superintendent of Police / Lead Investigator"),
        sa.Column("request_type", sa.String(length=50), nullable=False, server_default="disclosure"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("attachments", sa.JSON(), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("drafted_by", sa.Uuid(), nullable=False),
        sa.Column("submitted_by", sa.Uuid(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["drafted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sahyog_requests_case_id"), "sahyog_requests", ["case_id"], unique=False)
    op.create_index(op.f("ix_sahyog_requests_investigation_id"), "sahyog_requests", ["investigation_id"], unique=False)
    op.create_index(op.f("ix_sahyog_requests_report_id"), "sahyog_requests", ["report_id"], unique=False)
    op.create_index(op.f("ix_sahyog_requests_reference_number"), "sahyog_requests", ["reference_number"], unique=True)

    # 3. Create sahyog_status_history table
    op.create_table(
        "sahyog_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=False),
        sa.Column("to_status", sa.String(length=50), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["sahyog_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sahyog_status_history_request_id"), "sahyog_status_history", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sahyog_status_history_request_id"), table_name="sahyog_status_history")
    op.drop_table("sahyog_status_history")

    op.drop_index(op.f("ix_sahyog_requests_reference_number"), table_name="sahyog_requests")
    op.drop_index(op.f("ix_sahyog_requests_report_id"), table_name="sahyog_requests")
    op.drop_index(op.f("ix_sahyog_requests_investigation_id"), table_name="sahyog_requests")
    op.drop_index(op.f("ix_sahyog_requests_case_id"), table_name="sahyog_requests")
    op.drop_table("sahyog_requests")

    op.drop_index(op.f("ix_reports_investigation_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_case_id"), table_name="reports")
    op.drop_table("reports")
