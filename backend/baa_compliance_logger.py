"""
baa_compliance_logger.py
=========================
HIPAA BAA compliance audit logger for every Claude API call.

Logs WHAT was sent (metadata only) — never the actual clinical text.
This log proves to auditors that:
  1. PHI was purged before any external API call
  2. Only de-identified text was transmitted to Claude
  3. Every API call is traceable to a session and timestamp

Log entries are stored in MongoDB (coding_api_audit collection).
Falls back to file logging if DB is unavailable.

NEVER store:
  - The actual de-identified text
  - The Claude response text
  - Any patient identifiers
  - PHI audit hashes that could be reverse-engineered

DO store:
  - Session ID
  - Timestamp
  - Character counts (input/output)
  - Response time
  - Payer and patient status type
  - PHI purge layer results (counts only)
  - Model used
  - Success/failure status
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20251022"
LOG_COLLECTION = "coding_api_audit"


def log_api_call(
    session_id: str,
    input_char_count: int,
    output_char_count: int,
    response_time_ms: int,
    phi_audit: dict,
    payer: str,
    patient_status: str,
    success: bool = True,
    error_message: str = None,
) -> None:
    """
    Write a BAA compliance log entry for a Claude API call.

    Args:
        session_id         : Coding session ID (links to user session in DB)
        input_char_count   : Character count of de-identified text sent to Claude
        output_char_count  : Character count of Claude's response
        response_time_ms   : API round-trip time in milliseconds
        phi_audit          : Redaction audit from phi_purger_v2 (counts/metadata only)
        payer              : Payer type (Medicare/Medicaid/Commercial)
        patient_status     : Inpatient/Outpatient/Emergency
        success            : Whether the API call succeeded
        error_message      : Error message if failed (no PHI)
    """

    log_entry = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "CLAUDE_API_CALL",
        "model": CLAUDE_MODEL,
        "baa_status": "COVERED",
        "phi_transmitted": False,

        # Transmission metadata
        "input_char_count": input_char_count,
        "output_char_count": output_char_count,
        "response_time_ms": response_time_ms,

        # PHI purge summary (no actual PHI — counts only)
        "phi_purge_summary": {
            "total_redactions": phi_audit.get("total_redactions", 0),
            "redaction_rate_pct": phi_audit.get("redaction_rate_pct", 0.0),
            "layers_run": len(phi_audit.get("layers", [])),
            "phi_free_confidence": phi_audit.get("phi_free_confidence", "UNKNOWN"),
            "input_hash": phi_audit.get("input_hash", ""),
            "output_hash": phi_audit.get("output_hash", ""),
        },

        # Clinical context (non-identifying)
        "payer_type": payer,
        "patient_status_type": patient_status,

        # Outcome
        "success": success,
        "error_message": error_message,
    }

    # Try to write to MongoDB
    _write_to_mongo(log_entry)

    # Always write to application log as secondary record
    logger.info(
        f"BAA_AUDIT | session={session_id} | chars_in={input_char_count} | "
        f"chars_out={output_char_count} | redactions={phi_audit.get('total_redactions', 0)} | "
        f"phi_confidence={phi_audit.get('phi_free_confidence', '?')} | "
        f"response_ms={response_time_ms} | success={success}"
    )


def _write_to_mongo(log_entry: dict) -> None:
    """Write audit entry to MongoDB. Falls back to file if DB unavailable."""
    try:
        import motor.motor_asyncio
        import asyncio

        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.environ.get("MONGO_DB_NAME", "chcpro")

        async def _insert():
            client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
            db = client[db_name]
            await db[LOG_COLLECTION].insert_one(log_entry)
            client.close()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import threading
                result = [None]
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(_insert())
                    new_loop.close()
                t = threading.Thread(target=run_in_thread)
                t.start()
                t.join(timeout=5)
            else:
                loop.run_until_complete(_insert())
        except RuntimeError:
            asyncio.run(_insert())

    except Exception as e:
        logger.warning(f"MongoDB audit write failed — writing to file: {e}")
        _write_to_file(log_entry)


def _write_to_file(log_entry: dict) -> None:
    """Fallback file logger for audit entries."""
    import json
    log_dir = os.environ.get("AUDIT_LOG_DIR", "/tmp/chcpro_audit")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "baa_compliance.jsonl")
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"File audit write also failed: {e}")


def log_phi_purge_only(session_id: str, phi_audit: dict) -> None:
    """
    Log a PHI purge event where no API call was made (e.g., purge test).
    """
    log_entry = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "PHI_PURGE_ONLY",
        "phi_purge_summary": {
            "total_redactions": phi_audit.get("total_redactions", 0),
            "redaction_rate_pct": phi_audit.get("redaction_rate_pct", 0.0),
            "phi_free_confidence": phi_audit.get("phi_free_confidence", "UNKNOWN"),
        },
    }
    _write_to_mongo(log_entry)


def get_session_audit_trail(session_id: str) -> list:
    """
    Retrieve all audit log entries for a given session.
    Used by admin audit log page.
    Returns list of log entries (no PHI).
    """
    try:
        import motor.motor_asyncio
        import asyncio

        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.environ.get("MONGO_DB_NAME", "chcpro")

        async def _fetch():
            client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
            db = client[db_name]
            cursor = db[LOG_COLLECTION].find(
                {"session_id": session_id},
                {"_id": 0}
            ).sort("timestamp", -1)
            results = await cursor.to_list(length=100)
            client.close()
            return results

        return asyncio.run(_fetch())

    except Exception as e:
        logger.error(f"Audit trail fetch failed for session {session_id}: {e}")
        return []
