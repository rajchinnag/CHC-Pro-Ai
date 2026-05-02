"""
CHC Pro AI — Database Models (SQLAlchemy)
Tables: users, audit_log
Run migrations with Alembic: alembic upgrade head
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Index,
    String, Text, func, event
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """
    One row per registered provider.
    Cognito holds the auth credentials.
    This table holds the application-level profile and compliance data.
    """
    __tablename__ = "users"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cognito_sub           = Column(String(100), unique=True, nullable=False, index=True)
    email                 = Column(String(255), unique=True, nullable=False, index=True)

    # Provider identity
    first_name            = Column(String(100), nullable=False)
    last_name             = Column(String(100), nullable=False)
    organization          = Column(String(255), nullable=True)
    phone                 = Column(String(10),  nullable=False)

    # Professional credentials
    npi                   = Column(String(10),  nullable=False, index=True)
    tax_id_last4          = Column(String(4),   nullable=True)  # Only last 4 digits stored
    specialty             = Column(String(80),  nullable=False)
    state                 = Column(String(2),   nullable=False)
    provider_type         = Column(String(20),  nullable=False, default="individual")
    entity_type           = Column(String(1),   nullable=False, default="1")

    # Verification status
    npi_verified          = Column(Boolean, default=False, nullable=False)
    oig_clear             = Column(Boolean, default=False, nullable=False)
    pecos_enrolled        = Column(Boolean, default=False, nullable=False)
    email_verified        = Column(Boolean, default=False, nullable=False)
    mfa_enabled           = Column(Boolean, default=False, nullable=False)
    registration_complete = Column(Boolean, default=False, nullable=False)

    # E-Signature (HIPAA BAA)
    signature_id          = Column(String(64),  nullable=True)
    signed_at             = Column(DateTime(timezone=True), nullable=True)
    hipaa_baa_version     = Column(String(10),  nullable=True, default="v1.3")
    terms_version         = Column(String(10),  nullable=True, default="v2.1")
    privacy_version       = Column(String(10),  nullable=True, default="v2.0")

    # Preferences (populated later)
    claim_form_preference = Column(String(10),  nullable=True)

    # Timestamps
    created_at            = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at            = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_users_npi",   "npi"),
        Index("ix_users_state", "state"),
    )

    def __repr__(self):
        return f"<User {self.email} npi={self.npi}>"


class AuditLog(Base):
    """
    Immutable audit trail — insert only, never update or delete.
    HIPAA §164.312(b) requires 6-year retention.
    Enforce at DB level: REVOKE UPDATE, DELETE ON audit_log FROM app_user;
    """
    __tablename__ = "audit_log"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id     = Column(UUID(as_uuid=True), nullable=True, index=True)  # Nullable: pre-auth events
    action_type = Column(String(80), nullable=False, index=True)
    ip_address  = Column(INET, nullable=True)
    user_agent  = Column(Text, nullable=True)
    metadata    = Column(JSONB, nullable=True)  # Never store PHI or passwords here
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_user_id",    "user_id"),
        Index("ix_audit_action",     "action_type"),
        Index("ix_audit_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action_type} user={self.user_id} at={self.created_at}>"


# ── Action type constants ──────────────────────────────────────────────────

class AuditAction:
    REGISTRATION_STEP1    = "REGISTRATION_STEP1"
    NPI_VERIFIED          = "NPI_VERIFIED"
    OIG_CHECKED           = "OIG_CHECKED"
    OTP_SENT              = "OTP_SENT"
    OTP_VERIFIED          = "OTP_VERIFIED"
    PASSWORD_SET          = "PASSWORD_SET"
    MFA_SETUP             = "MFA_SETUP"
    MFA_VERIFIED          = "MFA_VERIFIED"
    ESIGNATURE_STORED     = "ESIGNATURE_STORED"
    REGISTRATION_COMPLETE = "REGISTRATION_COMPLETE"
    USER_LOGIN            = "USER_LOGIN"
    MFA_LOGIN             = "MFA_LOGIN"
    USER_LOGOUT           = "USER_LOGOUT"
    TOKEN_REFRESH         = "TOKEN_REFRESH"
    PASSWORD_RESET_INIT   = "PASSWORD_RESET_INIT"
    PASSWORD_RESET_DONE   = "PASSWORD_RESET_DONE"
    LOGIN_FAILED          = "LOGIN_FAILED"
    MFA_FAILED            = "MFA_FAILED"
