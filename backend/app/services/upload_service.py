"""
CHC Pro AI – Upload Service (Layer 2)
Handles: presigned URL generation, metadata stripping, status transitions.
PHI detection/purge is Layer 3 — this service only moves files safely.
"""
from __future__ import annotations
import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Allowed MIME types per format
MIME_MAP = {
    "pdf":   ["application/pdf"],
    "image": ["image/jpeg", "image/png", "image/tiff", "image/webp"],
    "hl7":   ["text/plain", "application/hl7-v2", "text/hl7"],
    "fhir":  ["application/fhir+json", "application/json"],
}

MAX_FILE_SIZE = 52_428_800  # 50 MB


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def generate_s3_key(user_id: str, upload_id: str, filename: str, stage: str = "raw") -> str:
    """
    Pattern: {stage}/{user_id}/{upload_id}/{filename}
    stage: raw | deidentified
    """
    safe_name = filename.replace(" ", "_")
    return f"{stage}/{user_id}/{upload_id}/{safe_name}"


async def create_presigned_upload_url(
    user_id: str,
    upload_id: str,
    filename: str,
    file_format: str,
    file_size_bytes: int,
) -> dict:
    """
    Generate a presigned S3 PUT URL for direct browser-to-S3 upload.
    Returns: {presigned_url, s3_key, expires_in}
    """
    s3_key = generate_s3_key(user_id, upload_id, filename, stage="raw")
    allowed_mimes = MIME_MAP.get(file_format, [])

    s3 = _s3_client()
    try:
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket_raw,
                "Key": s3_key,
                "ContentType": allowed_mimes[0] if allowed_mimes else "application/octet-stream",
                "ContentLength": file_size_bytes,
                "ServerSideEncryption": "AES256",
                "Metadata": {
                    "upload-id": upload_id,
                    "user-id": user_id,
                    "original-filename": filename,
                },
            },
            ExpiresIn=300,  # 5 minutes
        )
        return {
            "presigned_url": presigned_url,
            "s3_key": s3_key,
            "expires_in": 300,
        }
    except ClientError as e:
        logger.error(f"S3 presigned URL error: {e}")
        raise RuntimeError("Could not generate upload URL") from e


async def confirm_upload_in_s3(s3_key: str, bucket: str) -> bool:
    """Verify the file actually landed in S3 after client PUT."""
    s3 = _s3_client()
    try:
        s3.head_object(Bucket=bucket, Key=s3_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


async def strip_file_metadata(s3_key: str, upload_id: str) -> Optional[int]:
    """
    Download file, strip metadata (EXIF for images, XMP for PDFs),
    re-upload to same key. Returns file size in bytes or None on error.
    PDF metadata stripping requires pypdf; image stripping uses Pillow.
    This runs as a background task after confirm.
    """
    s3 = _s3_client()
    try:
        obj = s3.get_object(Bucket=settings.s3_bucket_raw, Key=s3_key)
        content_type = obj["ContentType"]
        raw_bytes = obj["Body"].read()

        cleaned_bytes = raw_bytes  # default: pass through

        if content_type == "application/pdf":
            cleaned_bytes = _strip_pdf_metadata(raw_bytes)
        elif content_type.startswith("image/"):
            cleaned_bytes = _strip_image_metadata(raw_bytes, content_type)

        # Re-upload stripped version
        s3.put_object(
            Bucket=settings.s3_bucket_raw,
            Key=s3_key,
            Body=cleaned_bytes,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        logger.info(f"Metadata stripped for upload {upload_id}, key {s3_key}")
        return len(cleaned_bytes)
    except Exception as e:
        logger.error(f"Metadata strip failed for {upload_id}: {e}")
        return None


def _strip_pdf_metadata(raw_bytes: bytes) -> bytes:
    """Remove PDF metadata using pypdf."""
    try:
        from pypdf import PdfReader, PdfWriter
        import io
        reader = PdfReader(io.BytesIO(raw_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        # Clear all metadata
        writer.add_metadata({})
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"PDF metadata strip skipped: {e}")
        return raw_bytes


def _strip_image_metadata(raw_bytes: bytes, content_type: str) -> bytes:
    """Remove EXIF/XMP from images using Pillow."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(raw_bytes))
        # Re-save without EXIF
        out = io.BytesIO()
        fmt = "JPEG" if "jpeg" in content_type else "PNG"
        img.save(out, format=fmt)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"Image metadata strip skipped: {e}")
        return raw_bytes


async def delete_raw_file(s3_key: str) -> bool:
    """
    Permanently delete the raw (pre-PHI-purge) file from S3.
    Called by Layer 3 after PHI purge is confirmed.
    """
    s3 = _s3_client()
    try:
        s3.delete_object(Bucket=settings.s3_bucket_raw, Key=s3_key)
        logger.info(f"Raw file deleted: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete raw file {s3_key}: {e}")
        return False


async def get_upload_list(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated upload history for a user."""
    from app.db.models import Upload, UploadContext

    offset = (page - 1) * page_size

    # Count total
    from sqlalchemy import func, select
    count_q = select(func.count()).where(Upload.user_id == user_id)
    total = (await db.execute(count_q)).scalar_one()

    # Fetch page with left join to context
    q = (
        select(Upload, UploadContext)
        .outerjoin(UploadContext, Upload.id == UploadContext.upload_id)
        .where(Upload.user_id == user_id)
        .order_by(Upload.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(q)).all()

    uploads = []
    for upload, ctx in rows:
        uploads.append({
            "upload_id": upload.id,
            "original_filename": upload.original_filename,
            "file_format": upload.file_format,
            "file_size_bytes": upload.file_size_bytes,
            "status": upload.status,
            "created_at": upload.created_at,
            "has_context": ctx is not None,
            "specialty": ctx.specialty if ctx else None,
            "payer_name": ctx.payer_name if ctx else None,
            "claim_form": ctx.claim_form if ctx else None,
        })

    return {"uploads": uploads, "total": total, "page": page, "page_size": page_size}
