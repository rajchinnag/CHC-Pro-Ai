"""
CHC Pro AI — Audit Log Service
Writes immutable audit events to PostgreSQL + CloudWatch Logs.
HIPAA §164.312(b) requires all access events to be logged.
"""
import json, logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AuditLog, AuditAction

log = logging.getLogger(__name__)


async def write_audit(
    db:          AsyncSession,
    action_type: str,
    user_id:     Optional[UUID] = None,
    ip_address:  Optional[str]  = None,
    user_agent:  Optional[str]  = None,
    metadata:    Optional[dict] = None,
) -> None:
    """
    Insert one audit log row. INSERT only — never UPDATE or DELETE.
    Metadata must never contain PHI, passwords, or full tax IDs.
    """
    # Sanitize metadata — strip any accidental sensitive fields
    safe_meta = {}
    if metadata:
        _blocked = {"password", "tax_id", "ssn", "signature_data", "totp_secret"}
        safe_meta = {k: v for k, v in metadata.items() if k.lower() not in _blocked}

    entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=safe_meta or None,
    )
    db.add(entry)
    # Caller commits via the session dependency

    # Also emit to application logger (picked up by CloudWatch agent)
    log.info(json.dumps({
        "audit":       True,
        "action":      action_type,
        "user_id":     str(user_id) if user_id else None,
        "ip":          ip_address,
        "meta_keys":   list(safe_meta.keys()),
    }))
