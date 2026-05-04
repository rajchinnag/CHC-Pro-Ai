"""0002_uploads

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-03

Adds: uploads, upload_context tables for Layer 2 file intake pipeline.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_format", sa.String(20), nullable=False),   # pdf, image, hl7, fhir
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("s3_key_raw", sa.String(512), nullable=True),     # set after upload
        sa.Column("s3_key_deidentified", sa.String(512), nullable=True),  # set after PHI purge
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        # pending → uploaded → ocr_complete → phi_purged → phi_verified → ready
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("ocr_text_length", sa.Integer(), nullable=True),
        sa.Column("phi_detected", sa.Boolean(), nullable=True),
        sa.Column("phi_purge_confirmed", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "upload_context",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("upload_id", UUID(as_uuid=True), sa.ForeignKey("uploads.id"), nullable=False, unique=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("specialty", sa.String(80), nullable=False),
        sa.Column("payer_name", sa.String(100), nullable=False),
        sa.Column("payer_type", sa.String(20), nullable=False),   # medicare, medicaid, commercial
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("claim_form", sa.String(10), nullable=False),   # cms1500, ub04
        sa.Column("code_sets", JSONB, nullable=False),            # ["ICD10CM","CPT","HCPCS"]
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("patient_dob_year", sa.Integer(), nullable=True),  # year only, not full DOB
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_uploads_user_id",   "uploads", ["user_id"],        if_not_exists=True)
    op.create_index("ix_uploads_status",    "uploads", ["status"],          if_not_exists=True)
    op.create_index("ix_uploads_created",   "uploads", ["created_at"],      if_not_exists=True)
    op.create_index("ix_ctx_upload_id",     "upload_context", ["upload_id"], if_not_exists=True)


def downgrade() -> None:
    op.drop_table("upload_context")
    op.drop_table("uploads")
