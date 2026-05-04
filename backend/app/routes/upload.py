"""
CHC Pro AI – Upload & Context Routes (Layer 2)
All routes require a valid JWT (auth_middleware).
"""
from __future__ import annotations
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.schemas.upload_schemas import (
    ContextRequest, ContextResponse,
    UploadConfirmRequest, UploadConfirmResponse,
    UploadDetail, UploadInitRequest, UploadInitResponse,
    UploadListResponse,
)
from app.services.upload_service import (
    confirm_upload_in_s3,
    create_presigned_upload_url,
    get_upload_list,
    strip_file_metadata,
)
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])


# ── Step 1: Initiate upload — get presigned S3 URL ────────────────────────────

@router.post("/init", response_model=UploadInitResponse, status_code=status.HTTP_201_CREATED)
async def initiate_upload(
    body: UploadInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Client calls this first. Returns a presigned S3 URL.
    Client then PUTs the file directly to S3 (never passes through our server).
    """
    from app.db.models import Upload

    user_id = current_user["sub"]
    upload_id = str(uuid.uuid4())

    # Generate presigned URL
    try:
        url_data = await create_presigned_upload_url(
            user_id=user_id,
            upload_id=upload_id,
            filename=body.original_filename,
            file_format=body.file_format,
            file_size_bytes=body.file_size_bytes,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Create upload record in DB
    upload = Upload(
        id=uuid.UUID(upload_id),
        user_id=uuid.UUID(user_id),
        original_filename=body.original_filename,
        file_format=body.file_format,
        file_size_bytes=body.file_size_bytes,
        s3_key_raw=url_data["s3_key"],
        status="pending",
    )
    db.add(upload)
    await db.commit()

    logger.info(f"Upload initiated: {upload_id} for user {user_id}")

    return UploadInitResponse(
        upload_id=upload_id,
        presigned_url=url_data["presigned_url"],
        s3_key=url_data["s3_key"],
        expires_in=url_data["expires_in"],
    )


# ── Step 2: Confirm upload — verify S3 receipt, trigger metadata strip ─────────

@router.post("/confirm", response_model=UploadConfirmResponse)
async def confirm_upload(
    body: UploadConfirmRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Client calls this after the S3 PUT completes.
    We verify the file exists in S3, update status, queue metadata strip.
    """
    from app.db.models import Upload
    from sqlalchemy import select, update

    user_id = current_user["sub"]

    # Fetch upload record
    result = await db.execute(
        select(Upload).where(
            Upload.id == body.upload_id,
            Upload.user_id == uuid.UUID(user_id),
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.status != "pending":
        raise HTTPException(status_code=409, detail=f"Upload already in status: {upload.status}")

    # Verify file is in S3
    exists = await confirm_upload_in_s3(upload.s3_key_raw, settings.s3_bucket_raw)
    if not exists:
        raise HTTPException(status_code=422, detail="File not found in S3 — upload may have failed")

    # Update status
    await db.execute(
        update(Upload)
        .where(Upload.id == body.upload_id)
        .values(status="uploaded")
    )
    await db.commit()

    # Queue metadata strip as background task
    background_tasks.add_task(
        strip_file_metadata,
        s3_key=upload.s3_key_raw,
        upload_id=str(body.upload_id),
    )

    logger.info(f"Upload confirmed: {body.upload_id}")
    return UploadConfirmResponse(
        upload_id=body.upload_id,
        status="uploaded",
        message="File received. Metadata stripping queued.",
    )


# ── Step 3: Submit context form ────────────────────────────────────────────────

@router.post("/context", response_model=ContextResponse, status_code=status.HTTP_201_CREATED)
async def submit_context(
    body: ContextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit the clinical context for an upload.
    Must be called after /confirm. Triggers Layer 3 PHI pipeline.
    """
    from app.db.models import Upload, UploadContext
    from sqlalchemy import select

    user_id = current_user["sub"]

    # Verify upload belongs to user
    result = await db.execute(
        select(Upload).where(
            Upload.id == body.upload_id,
            Upload.user_id == uuid.UUID(user_id),
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.status == "pending":
        raise HTTPException(status_code=409, detail="File not yet confirmed. Call /confirm first.")

    # Check no context already submitted
    existing = await db.execute(
        select(UploadContext).where(UploadContext.upload_id == body.upload_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Context already submitted for this upload")

    # Save context
    ctx = UploadContext(
        id=uuid.uuid4(),
        upload_id=body.upload_id,
        user_id=uuid.UUID(user_id),
        specialty=body.specialty,
        payer_name=body.payer_name,
        payer_type=body.payer_type,
        state=body.state,
        claim_form=body.claim_form,
        code_sets=body.code_sets,
        visit_date=body.visit_date,
        patient_dob_year=body.patient_dob_year,
        notes=body.notes,
    )
    db.add(ctx)

    # Update upload status to context_complete
    from sqlalchemy import update
    await db.execute(
        update(Upload)
        .where(Upload.id == body.upload_id)
        .values(status="context_complete")
    )
    await db.commit()

    logger.info(f"Context submitted for upload {body.upload_id}")

    # TODO Layer 3: trigger PHI pipeline here
    # background_tasks.add_task(run_phi_pipeline, upload_id=body.upload_id)

    return ContextResponse(
        context_id=ctx.id,
        upload_id=body.upload_id,
        status="context_complete",
        message="Context saved. Ready for PHI pipeline (Layer 3).",
    )


# ── Upload history ─────────────────────────────────────────────────────────────

@router.get("/history", response_model=UploadListResponse)
async def get_upload_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return paginated upload history for the current user."""
    user_id = current_user["sub"]
    data = await get_upload_list(db, user_id, page, page_size)
    return UploadListResponse(**data)


# ── Upload detail ──────────────────────────────────────────────────────────────

@router.get("/{upload_id}", response_model=UploadDetail)
async def get_upload_detail(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return full detail for a single upload including context."""
    from app.db.models import Upload, UploadContext
    from sqlalchemy import select

    user_id = current_user["sub"]

    result = await db.execute(
        select(Upload).where(
            Upload.id == upload_id,
            Upload.user_id == uuid.UUID(user_id),
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    ctx_result = await db.execute(
        select(UploadContext).where(UploadContext.upload_id == upload_id)
    )
    ctx = ctx_result.scalar_one_or_none()

    return UploadDetail(
        upload_id=upload.id,
        original_filename=upload.original_filename,
        file_format=upload.file_format,
        file_size_bytes=upload.file_size_bytes,
        status=upload.status,
        page_count=upload.page_count,
        phi_detected=upload.phi_detected,
        phi_purge_confirmed=upload.phi_purge_confirmed,
        error_message=upload.error_message,
        created_at=upload.created_at,
        updated_at=upload.updated_at,
        context=ctx,
    )


# ── Delete upload ──────────────────────────────────────────────────────────────

@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an upload and its S3 files.
    Only allowed if status is pending, uploaded, or error.
    """
    from app.db.models import Upload
    from app.services.upload_service import delete_raw_file
    from sqlalchemy import select, delete

    user_id = current_user["sub"]

    result = await db.execute(
        select(Upload).where(
            Upload.id == upload_id,
            Upload.user_id == uuid.UUID(user_id),
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.status not in ("pending", "uploaded", "error"):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete upload in current status. Contact support.",
        )

    # Delete from S3
    if upload.s3_key_raw:
        await delete_raw_file(upload.s3_key_raw)

    # Delete DB records
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(Upload).where(Upload.id == upload_id))
    await db.commit()

    logger.info(f"Upload deleted: {upload_id} by user {user_id}")
