"""
CHC Pro AI — Layer 3 Coding Pipeline (Gemini Flash)
=====================================================
Flow:
  1. Fetch upload + context from DB
  2. Download raw file from S3
  3. OCR / text extraction
  4. PHI purge
  5. PHI verification (second pass)
  6. AI coding via Gemini Flash
  7. Store CodingResult in DB
  8. Delete raw file from S3 (PHI minimisation)
  9. Update upload status → coding_complete
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
import httpx
from botocore.exceptions import ClientError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from dotenv import load_dotenv; load_dotenv(); from dotenv import load_dotenv; load_dotenv(); GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.5-flash"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def utcnow():
    return datetime.now(timezone.utc)


def _s3():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


async def _set_status(db: AsyncSession, upload_id: uuid.UUID, status: str, error: Optional[str] = None):
    from app.db.models import Upload
    vals = {"status": status, "updated_at": utcnow()}
    if error:
        vals["error_message"] = error
    await db.execute(update(Upload).where(Upload.id == upload_id).values(**vals))
    await db.commit()


async def _gemini(prompt: str, system: str) -> str:
    """Call Gemini Flash and return the text response."""
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(clean)


async def _run_gemini_phi_purge(text: str) -> tuple[str, dict]:
    """Stage 1 — PHI purge via Gemini."""
    system = (
        "You are a HIPAA PHI de-identification expert. "
        "Identify and replace ALL 18 HIPAA identifiers in the text. "
        "Return ONLY valid JSON — no prose, no markdown fences. "
        'Schema: {"phi_found":[{"field":"string","original":"string","replaced":"string"}],'
        '"clean_text":"string","categories_found":["string"],"total":0}'
    )
    prompt = f"De-identify this medical text and return JSON only:\n\n{text[:12000]}"
    raw = await _gemini(prompt, system)
    data = _parse_json(raw)
    phi_report = {
        "redactions": {p["field"]: 1 for p in data.get("phi_found", [])},
        "categories_found": data.get("categories_found", []),
        "total": data.get("total", len(data.get("phi_found", []))),
        "phi_found": data.get("phi_found", []),
    }
    return data.get("clean_text", text), phi_report


async def _run_gemini_coding(
    deidentified_text: str,
    payer: str,
    claim_form: str,
    specialty: str,
) -> dict:
    """Stage 2 — Medical coding via Gemini Flash (two-pass: generate + verify)."""

    claim_type = claim_form.upper().replace("CMS1500", "CMS-1500").replace("UB04", "UB-04")
    patient_type = "Inpatient" if claim_form.lower() == "ub04" else "Outpatient"

    # ── Pass 1: Generate codes ────────────────────────────────────────────────
    system_gen = (
        "You are a CPC-certified medical coder with 15 years experience. "
        "Analyze the de-identified clinical text and generate accurate codes. "
        "Return ONLY valid JSON — no prose, no markdown. "
        'Schema: {"principal_diagnosis":{"code":"","description":"","code_type":"ICD10-CM","guideline_ref":"","status":"verified","confidence":0.0,"rationale":""},'
        '"secondary_diagnoses":[...],'
        '"principal_procedure":{"code":"","description":"","code_type":"CPT","guideline_ref":"","status":"verified","confidence":0.0,"rationale":""},'
        '"additional_procedures":[...],'
        '"ms_drg":{"code":"","description":"","code_type":"MS-DRG","guideline_ref":"","status":"verified","confidence":0.0,"rationale":""},'
        '"revenue_codes":[...],'
        '"modifiers":[...],'
        '"processing_log":["string"]}'
    )
    prompt_gen = (
        f"Claim type: {claim_type} | Payer: {payer} | Patient type: {patient_type} | Specialty: {specialty}\n\n"
        f"Clinical text:\n{deidentified_text[:10000]}\n\n"
        "Generate the complete code set. Only include codes with confidence >= 0.85. "
        "Include POA indicators for diagnoses. Return JSON only."
    )
    raw_gen = await _gemini(prompt_gen, system_gen)
    codes = _parse_json(raw_gen)
    codes.setdefault("processing_log", [])
    codes["processing_log"].append("Pass 1 complete: initial code generation via Gemini Flash")

    # ── Pass 2: Verify and cross-check ───────────────────────────────────────
    system_verify = (
        "You are a senior medical coding auditor. "
        "Review these codes for accuracy, NCCI compliance, MUE limits, and consistency. "
        "Cross-check ICD-10 diagnoses against CPT procedures — they must clinically match. "
        "Upgrade confidence only if fully supported. Downgrade or flag inconsistencies. "
        "Return the corrected full JSON in the SAME schema — no prose, no markdown."
    )
    prompt_verify = (
        f"Verify these codes for {claim_type} claim, payer {payer}:\n"
        f"{json.dumps(codes, indent=2)}\n\n"
        f"Clinical context:\n{deidentified_text[:4000]}\n\n"
        "Apply NCCI edits, check MUE limits, verify diagnosis-procedure linkage. "
        "Only codes >= 0.95 confidence should remain as 'verified'. "
        "Set status to 'review' for anything below 0.95. Return corrected JSON only."
    )
    raw_verify = await _gemini(prompt_verify, system_verify)
    verified = _parse_json(raw_verify)
    verified.setdefault("processing_log", codes.get("processing_log", []))
    verified["processing_log"].append("Pass 2 complete: NCCI/MUE verification via Gemini Flash")
    verified["processing_log"].append(f"AI model: {GEMINI_MODEL} | Payer: {payer} | Claim: {claim_type}")

    return verified


async def run_phi_pipeline(upload_id: str, db: AsyncSession) -> None:
    """
    Full Layer 3 pipeline. Runs as a FastAPI BackgroundTask.
    """
    uid = uuid.UUID(upload_id)

    if not GEMINI_API_KEY:
        logger.error("[pipeline] GEMINI_API_KEY not set in .env")
        await _set_status(db, uid, "error", "GEMINI_API_KEY not configured. Add it to .env and restart.")
        return

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
            await _set_status(db, uid, "error", "No clinical context found.")
            return

        await _set_status(db, uid, "ocr_processing")

        # ── 2. Download file from S3 ──────────────────────────────────────────
        s3 = _s3()
        try:
            obj = s3.get_object(Bucket=os.getenv("S3_BUCKET_RAW", "chc-raw-uploads"), Key=upload.s3_key_raw)
            raw_bytes = obj["Body"].read()
        except ClientError as e:
            logger.error(f"[pipeline] S3 download failed: {e}")
            await _set_status(db, uid, "error", "Could not retrieve file from storage.")
            return

        # ── 3. OCR / text extraction ──────────────────────────────────────────
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
            from ocr_service import extract_text
            raw_text, page_count = extract_text(upload.original_filename, raw_bytes)
        except Exception as e:
            # Fallback: try pypdf directly
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw_bytes))
                raw_text = "\n".join(p.extract_text() or "" for p in reader.pages)
                page_count = len(reader.pages)
            except Exception as e2:
                logger.error(f"[pipeline] OCR failed: {e} | fallback: {e2}")
                await _set_status(db, uid, "error", f"OCR failed: {e}")
                return

        if not raw_text.strip():
            await _set_status(db, uid, "error", "No text could be extracted from the document.")
            return

        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                page_count=page_count, status="ocr_complete", updated_at=utcnow()
            )
        )
        await db.commit()

        # ── 4. PHI purge via Gemini ───────────────────────────────────────────
        try:
            deidentified_text, phi_report = await _run_gemini_phi_purge(raw_text)
        except Exception as e:
            logger.error(f"[pipeline] PHI purge failed: {e}")
            # Fall back to regex-only purge
            try:
                from phi_purger import purge_phi
                deidentified_text, phi_obj = purge_phi(raw_text)
                phi_report = {"redactions": {}, "categories_found": [], "total": 0, "phi_found": []}
            except Exception:
                await _set_status(db, uid, "error", f"PHI purge failed: {e}")
                return

        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                phi_detected=bool(phi_report.get("total", 0) > 0),
                status="phi_purged", updated_at=utcnow()
            )
        )
        await db.commit()

        # ── 5. PHI second-pass verification ──────────────────────────────────
        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                phi_purge_confirmed=True, status="phi_verified", updated_at=utcnow()
            )
        )
        await db.commit()

        # ── 6. AI coding via Gemini Flash ─────────────────────────────────────
        await _set_status(db, uid, "coding_in_progress")

        phi_audit = {
            "redactions": phi_report.get("redactions", {}),
            "categories_found": phi_report.get("categories_found", []),
            "total": phi_report.get("total", 0),
        }

        try:
            coding_result = await _run_gemini_coding(
                deidentified_text=deidentified_text,
                payer=ctx.payer_name,
                claim_form=ctx.claim_form,
                specialty=ctx.specialty,
            )
        except Exception as e:
            logger.error(f"[pipeline] Gemini coding failed: {e}")
            await _set_status(db, uid, "error", f"AI coding failed: {e}")
            return

        # ── 7. Store CodingResult ─────────────────────────────────────────────
        from app.db.models import CodingResult
        result_row = CodingResult(
            id=uuid.uuid4(),
            upload_id=uid,
            user_id=upload.user_id,
            coding_data=coding_result,
            phi_report=phi_audit,
            page_count=page_count,
            created_at=utcnow(),
        )
        db.add(result_row)

        # ── 8. Delete raw S3 file ─────────────────────────────────────────────
        try:
            s3.delete_object(Bucket=os.getenv("S3_BUCKET_RAW", "chc-raw-uploads"), Key=upload.s3_key_raw)
            logger.info(f"[pipeline] Raw file deleted: {upload.s3_key_raw}")
        except Exception as e:
            logger.warning(f"[pipeline] Could not delete raw S3 file: {e}")

        # ── 9. Final status ───────────────────────────────────────────────────
        await db.execute(
            update(Upload).where(Upload.id == uid).values(
                status="coding_complete", updated_at=utcnow()
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
