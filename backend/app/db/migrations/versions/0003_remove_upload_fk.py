"""Remove FK constraint on uploads.user_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-30
"""
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('uploads_user_id_fkey', 'uploads', type_='foreignkey')
    op.drop_constraint('upload_context_user_id_fkey', 'upload_context', type_='foreignkey')


def downgrade() -> None:
    pass
