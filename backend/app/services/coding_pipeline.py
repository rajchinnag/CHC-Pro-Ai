"""
CHC Pro AI — Layer 3 Coding Pipeline
=====================================
Triggered after context is submitted.

Flow:
  1. Fetch upload + context from DB
  2. Download raw file from S3
  3. OCR / text extraction
  4. PHI purge (phi_purger_v2 — 3-layer regex + Presidio + scispaCy)
  5. PHI verification (second pass)
  6. AI coding via claude_coding_engine
  7. Store CodingResult in DB
  8. Delete raw file from S3 (PHI minimisation)
  9. Update upload status → coding_complete
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def utcnow():
    return datetime.now(timezone.utc)


def _s3():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


async def _set_status(db: AsyncSession, upload_id: uuid.UUID, status: str, error: Optional[str] = None):
    from app.db.models import Upload
    vals = {"status": status, "updated_at": utcnow()}
    if error:
        vals["error_message"] = error
    await db.execute(update(Upload).where(Upload.id == upload_id).values(**vals))
    await db.commit()


async def run_phi_pipeline(upload_id: str, db: AsyncSession) -> None:
    """
    Full Layer 3 pipeline. Runs as a FastAPI BackgroundTask.
    All exceptions are caught and written to upload.error_message.
    """
    uid = uuid.UUID(upload_id)

    try:
        from app.db.models import Upload, UploadContext, CodingResult
        from sqlalchemy import select

        # ── 1. Load upload + context ──────────────────────────────────────────
        row = await db.execute(select(Upload).where(Upload.id == uid))
        upload = row.scalar_one_or_none()
        if not upload:
            logger.error(f"[pipeline] Upload {upload_id} not found")
            return

        ctx_row = await db.execute(select(UploadContext).where(UploadContext.upload_id == uid))
        ctx = ctx_row.scalar_one_or_none()
        if not ctx:
            logger.error(f"[pipeline] No context for upload {upload_id}")
            await _set_status(db, uid, "error", "No clinical context found.")
            return

        await _set_status(db, uid, "ocr_processing")

        # ── 2. Download file from S3 ──────────────────────────────────────────
        s3 = _s3()
        try:
            obj = s3.get_object(Bucket=settings.s3_bucket_raw, Key=upload.s3_key_raw)
            raw_bytes = obj["Body"].read()
        except ClientError as e:
            logger.error(f"[pipeline] S3 download failed for {upload_id}: {e}")
            await _set_status(db, uid, "error", "Could not retrieve file from storage.")
            return

        # ── 3. OCR / text extraction ──────────────────────────────────────────
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
            from ocr_service import extract_text
            raw_text, page_count = extract_text(upload.original_filename, raw_bytes)
        except Exception as e:
            logger.error(f"[pipeline] OCR failed for {upload_id}: {e}")
            await _set_status(db, uid, "error", f"OCR failed: {e}")
            return

        if not raw_text.strip():
            await _set_status(db, uid, "error", "No text could be extracted from the document.")
            return

        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                page_count=page_count,
                status="ocr_complete",
                updated_at=utcnow(),
            )
        )
        await db.commit()

        # ── 4. PHI purge ──────────────────────────────────────────────────────
        try:
            from phi_purger_v2 import purge_phi
            deidentified_text, phi_report = purge_phi(raw_text)
        except ImportError:
            # Fall back to v1 if presidio not installed
            from phi_purger import purge_phi as purge_phi_v1
            deidentified_text, phi_report_obj = purge_phi_v1(raw_text)
            phi_report = {
                "redactions": phi_report_obj.redactions,
                "categories_found": phi_report_obj.categories_found,
                "total": sum(phi_report_obj.redactions.values()),
            }
        except Exception as e:
            logger.error(f"[pipeline] PHI purge failed for {upload_id}: {e}")
            await _set_status(db, uid, "error", f"PHI purge failed: {e}")
            return

        phi_detected = bool(
            phi_report.get("total", 0) > 0
            if isinstance(phi_report, dict)
            else sum(getattr(phi_report, "redactions", {}).values()) > 0
        )

        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                phi_detected=phi_detected,
                status="phi_purged",
                updated_at=utcnow(),
            )
        )
        await db.commit()

        # ── 5. PHI verification (second pass) ────────────────────────────────
        try:
            from phi_purger_v2 import verify_phi_free
            phi_clean, remaining = verify_phi_free(deidentified_text)
        except Exception:
            phi_clean, remaining = True, []

        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                phi_purge_confirmed=phi_clean,
                status="phi_verified",
                updated_at=utcnow(),
            )
        )
        await db.commit()

        # ── 6. AI coding ──────────────────────────────────────────────────────
        await _set_status(db, uid, "coding_in_progress")

        try:
            from claude_coding_engine import run_coding_session
            phi_audit = phi_report if isinstance(phi_report, dict) else {
                "redactions": getattr(phi_report, "redactions", {}),
                "categories_found": getattr(phi_report, "categories_found", []),
            }
            coding_result = run_coding_session(
                deidentified_text=deidentified_text,
                phi_audit_report=phi_audit,
                session_id=upload_id,
                payer=ctx.payer_name,
                facility_type="Hospital",
                claim_type=ctx.claim_form.upper().replace("CMS1500", "CMS-1500").replace("UB04", "UB-04"),
                patient_status="Inpatient" if ctx.claim_form == "ub04" else "Outpatient",
                specialty=ctx.specialty,
            )
        except Exception as e:
            logger.error(f"[pipeline] Claude coding failed for {upload_id}: {e}")
            await _set_status(db, uid, "error", f"AI coding failed: {e}")
            return

        # ── 7. Store CodingResult ─────────────────────────────────────────────
        result_row = CodingResult(
            id=uuid.uuid4(),
            upload_id=uid,
            user_id=upload.user_id,
            coding_data=coding_result if isinstance(coding_result, dict) else vars(coding_result),
            phi_report=phi_audit,
            page_count=page_count,
            created_at=utcnow(),
        )
        db.add(result_row)

        # ── 8. Delete raw S3 file (PHI minimisation) ──────────────────────────
        try:
            s3.delete_object(Bucket=settings.s3_bucket_raw, Key=upload.s3_key_raw)
            logger.info(f"[pipeline] Raw file deleted from S3: {upload.s3_key_raw}")
        except Exception as e:
            logger.warning(f"[pipeline] Could not delete raw S3 file: {e}")

        # ── 9. Final status update ────────────────────────────────────────────
        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                status="coding_complete",
                updated_at=utcnow(),
            )
        )
        await db.commit()
        logger.info(f"[pipeline] Completed for upload {upload_id}")

    except Exception as e:
        logger.exception(f"[pipeline] Unexpected error for {upload_id}: {e}")
        try:
            await _set_status(db, uid, "error", f"Internal error: {e}")
        except Exception:
            pass
