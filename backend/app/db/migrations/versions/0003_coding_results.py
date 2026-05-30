"""0003_coding_results

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-30

Adds: coding_results table for Layer 3 AI coding output.
Also adds: ocr_processing, coding_in_progress status support (no schema change needed).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coding_results",
        sa.Column("id",          postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id"), nullable=False, unique=True),
        sa.Column("user_id",     postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"),   nullable=False),
        sa.Column("coding_data", postgresql.JSONB, nullable=False),
        sa.Column("phi_report",  postgresql.JSONB, nullable=True),
        sa.Column("page_count",  sa.Integer, nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_coding_results_upload_id", "coding_results", ["upload_id"])
    op.create_index("ix_coding_results_user_id",   "coding_results", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_coding_results_user_id",   table_name="coding_results")
    op.drop_index("ix_coding_results_upload_id", table_name="coding_results")
    op.drop_table("coding_results")
