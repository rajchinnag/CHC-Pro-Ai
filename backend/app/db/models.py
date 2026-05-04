"""
CHC Pro AI – Database Models (SQLAlchemy)
Tables: users, audit_log, uploads, upload_context
Run migrations with Alembic: alembic upgrade head
"""
import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Date, Index,
    Integer, String, Text, func, ForeignKey
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cognito_sub           = Column(String(100), unique=True, nullable=False, index=True)
    email                 = Column(String(255), unique=True, nullable=False, index=True)
    first_name            = Column(String(100), nullable=False)
    last_name             = Column(String(100), nullable=False)
    organization          = Column(String(255), nullable=True)
    phone                 = Column(String(10),  nullable=False)
    npi                   = Column(String(10),  nullable=False, index=True)
    tax_id_last4          = Column(String(4),   nullable=True)
    specialty             = Column(String(80),  nullable=False)
    state                 = Column(String(2),   nullable=False)
    provider_type         = Column(String(20),  nullable=False, default="individual")
    entity_type           = Column(String(1),   nullable=False, default="1")
    npi_verified          = Column(Boolean, default=False, nullable=False)
    oig_clear             = Column(Boolean, default=False, nullable=False)
    pecos_enrolled        = Column(Boolean, default=False, nullable=False)
    email_verified        = Column(Boolean, default=False, nullable=False)
    mfa_enabled           = Column(Boolean, default=False, nullable=False)
    registration_complete = Column(Boolean, default=False, nullable=False)
    signature_id          = Column(String(64),  nullable=True)
    signed_at             = Column(DateTime(timezone=True), nullable=True)
    hipaa_baa_version     = Column(String(10),  nullable=True, default="v1.3")
    terms_version         = Column(String(10),  nullable=True, default="v2.1")
    privacy_version       = Column(String(10),  nullable=True, default="v2.0")
    claim_form_preference = Column(String(10),  nullable=True)
    created_at            = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at            = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    uploads               = relationship("Upload", back_populates="user", lazy="select")

    __table_args__ = (
        Index("ix_users_npi",   "npi"),
        Index("ix_users_state", "state"),
    )

    def __repr__(self):
        return f"<User {self.email} npi={self.npi}>"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id     = Column(UUID(as_uuid=True), nullable=True, index=True)
    action_type = Column(String(80), nullable=False, index=True)
    ip_address  = Column(INET, nullable=True)
    user_agent  = Column(Text, nullable=True)
    extra_data  = Column(JSONB, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_user_id",    "user_id"),
        Index("ix_audit_action",     "action_type"),
        Index("ix_audit_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action_type} user={self.user_id}>"


class Upload(Base):
    """
    One row per file upload.
    Tracks the full lifecycle from upload → OCR → PHI purge → ready for coding.
    """
    __tablename__ = "uploads"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    original_filename   = Column(String(255), nullable=False)
    file_format         = Column(String(20),  nullable=False)   # pdf, image, hl7, fhir
    file_size_bytes     = Column(BigInteger,  nullable=False)
    s3_key_raw          = Column(String(512), nullable=True)
    s3_key_deidentified = Column(String(512), nullable=True)
    status              = Column(String(30),  nullable=False, default="pending")
    # Status flow: pending → uploaded → context_complete → ocr_complete
    #              → phi_purged → phi_verified → ready → coding_complete
    page_count          = Column(Integer,  nullable=True)
    ocr_text_length     = Column(Integer,  nullable=True)
    phi_detected        = Column(Boolean,  nullable=True)
    phi_purge_confirmed = Column(Boolean,  nullable=True)
    error_message       = Column(Text,     nullable=True)
    created_at          = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at          = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user    = relationship("User", back_populates="uploads")
    context = relationship("UploadContext", back_populates="upload", uselist=False)

    __table_args__ = (
        Index("ix_uploads_user_id", "user_id"),
        Index("ix_uploads_status",  "status"),
        Index("ix_uploads_created", "created_at"),
    )

    def __repr__(self):
        return f"<Upload {self.original_filename} status={self.status}>"


class UploadContext(Base):
    """
    Clinical context for an upload — what codes are needed, which payer, etc.
    One-to-one with Upload.
    """
    __tablename__ = "upload_context"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id        = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=False, unique=True)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    specialty        = Column(String(80),  nullable=False)
    payer_name       = Column(String(100), nullable=False)
    payer_type       = Column(String(20),  nullable=False)   # medicare, medicaid, commercial
    state            = Column(String(2),   nullable=False)
    claim_form       = Column(String(10),  nullable=False)   # cms1500, ub04
    code_sets        = Column(JSONB,       nullable=False)   # ["ICD10CM","CPT","HCPCS"]
    visit_date       = Column(Date,        nullable=True)
    patient_dob_year = Column(Integer,     nullable=True)
    notes            = Column(Text,        nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    upload = relationship("Upload", back_populates="context")

    def __repr__(self):
        return f"<UploadContext upload={self.upload_id} payer={self.payer_type}>"


# ── Audit action constants ─────────────────────────────────────────────────────

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
    UPLOAD_INITIATED      = "UPLOAD_INITIATED"
    UPLOAD_CONFIRMED      = "UPLOAD_CONFIRMED"
    CONTEXT_SUBMITTED     = "CONTEXT_SUBMITTED"
    UPLOAD_DELETED        = "UPLOAD_DELETED"
