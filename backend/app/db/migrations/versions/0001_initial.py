"""Initial: users and audit_log tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id',                    postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cognito_sub',           sa.String(100), unique=True,  nullable=False),
        sa.Column('email',                 sa.String(255), unique=True,  nullable=False),
        sa.Column('first_name',            sa.String(100), nullable=False),
        sa.Column('last_name',             sa.String(100), nullable=False),
        sa.Column('organization',          sa.String(255), nullable=True),
        sa.Column('phone',                 sa.String(10),  nullable=False),
        sa.Column('npi',                   sa.String(10),  nullable=False),
        sa.Column('tax_id_last4',          sa.String(4),   nullable=True),
        sa.Column('specialty',             sa.String(80),  nullable=False),
        sa.Column('state',                 sa.String(2),   nullable=False),
        sa.Column('provider_type',         sa.String(20),  nullable=False, server_default='individual'),
        sa.Column('entity_type',           sa.String(1),   nullable=False, server_default='1'),
        sa.Column('npi_verified',          sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('oig_clear',             sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pecos_enrolled',        sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verified',        sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_enabled',           sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('registration_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('signature_id',          sa.String(64),  nullable=True),
        sa.Column('signed_at',             sa.DateTime(timezone=True), nullable=True),
        sa.Column('hipaa_baa_version',     sa.String(10),  nullable=True),
        sa.Column('terms_version',         sa.String(10),  nullable=True),
        sa.Column('privacy_version',       sa.String(10),  nullable=True),
        sa.Column('claim_form_preference', sa.String(10),  nullable=True),
        sa.Column('created_at',            sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at',            sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )
    op.create_index('ix_users_cognito_sub', 'users', ['cognito_sub'], unique=True)
    op.create_index('ix_users_email',       'users', ['email'],       unique=True)
    op.create_index('ix_users_npi',         'users', ['npi'])
    op.create_index('ix_users_state',       'users', ['state'])

    op.create_table(
        'audit_log',
        sa.Column('id',          sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id',     postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(80),   nullable=False),
        sa.Column('ip_address',  postgresql.INET(), nullable=True),
        sa.Column('user_agent',  sa.Text(),        nullable=True),
        sa.Column('metadata',    postgresql.JSONB(), nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
    )
    op.create_index('ix_audit_user_id',    'audit_log', ['user_id'])
    op.create_index('ix_audit_action',     'audit_log', ['action_type'])
    op.create_index('ix_audit_created_at', 'audit_log', ['created_at'])

    # Revoke UPDATE and DELETE from application role — audit log is immutable
    op.execute("DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='app_user') THEN "
               "REVOKE UPDATE, DELETE ON audit_log FROM app_user; END IF; END $$;")


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('users')
