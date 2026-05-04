"""
CHC Pro AI – Upload & Context Schemas (Layer 2)
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ── Allowed values ─────────────────────────────────────────────────────────────

ALLOWED_FORMATS   = {"pdf", "image", "hl7", "fhir"}
ALLOWED_PAYER     = {"medicare", "medicaid", "commercial", "tricare", "va"}
ALLOWED_FORMS     = {"cms1500", "ub04"}
ALLOWED_CODESETS  = {"ICD10CM", "ICD10PCS", "CPT", "HCPCS", "DRG"}
ALLOWED_STATES    = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
}


# ── Upload initiation ──────────────────────────────────────────────────────────

class UploadInitRequest(BaseModel):
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_format: str       = Field(..., description="pdf | image | hl7 | fhir")
    file_size_bytes: int   = Field(..., gt=0, le=52_428_800)  # 50 MB max

    @field_validator("file_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.lower()
        if v not in ALLOWED_FORMATS:
            raise ValueError(f"file_format must be one of {ALLOWED_FORMATS}")
        return v

    @field_validator("original_filename")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename")
        return v


class UploadInitResponse(BaseModel):
    upload_id: UUID
    presigned_url: str
    s3_key: str
    expires_in: int = 300  # seconds


# ── Upload confirmation (after client puts file to S3) ─────────────────────────

class UploadConfirmRequest(BaseModel):
    upload_id: UUID
    etag: Optional[str] = None


class UploadConfirmResponse(BaseModel):
    upload_id: UUID
    status: str
    message: str


# ── Context form ───────────────────────────────────────────────────────────────

class ContextRequest(BaseModel):
    upload_id: UUID
    specialty: str        = Field(..., min_length=2, max_length=80)
    payer_name: str       = Field(..., min_length=2, max_length=100)
    payer_type: str       = Field(..., description="medicare|medicaid|commercial|tricare|va")
    state: str            = Field(..., min_length=2, max_length=2)
    claim_form: str       = Field(..., description="cms1500 | ub04")
    code_sets: List[str]  = Field(..., min_length=1)
    visit_date: Optional[date]    = None
    patient_dob_year: Optional[int] = Field(None, ge=1900, le=2025)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("payer_type")
    @classmethod
    def validate_payer(cls, v: str) -> str:
        v = v.lower()
        if v not in ALLOWED_PAYER:
            raise ValueError(f"payer_type must be one of {ALLOWED_PAYER}")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.upper()
        if v not in ALLOWED_STATES:
            raise ValueError("Invalid US state code")
        return v

    @field_validator("claim_form")
    @classmethod
    def validate_form(cls, v: str) -> str:
        v = v.lower()
        if v not in ALLOWED_FORMS:
            raise ValueError(f"claim_form must be one of {ALLOWED_FORMS}")
        return v

    @field_validator("code_sets")
    @classmethod
    def validate_codesets(cls, v: List[str]) -> List[str]:
        invalid = set(v) - ALLOWED_CODESETS
        if invalid:
            raise ValueError(f"Unknown code sets: {invalid}")
        return v


class ContextResponse(BaseModel):
    context_id: UUID
    upload_id: UUID
    status: str
    message: str


# ── Upload list / history ──────────────────────────────────────────────────────

class UploadSummary(BaseModel):
    upload_id: UUID
    original_filename: str
    file_format: str
    file_size_bytes: int
    status: str
    created_at: datetime
    has_context: bool
    specialty: Optional[str] = None
    payer_name: Optional[str] = None
    claim_form: Optional[str] = None

    model_config = {"from_attributes": True}


class UploadListResponse(BaseModel):
    uploads: List[UploadSummary]
    total: int
    page: int
    page_size: int


# ── Upload detail ──────────────────────────────────────────────────────────────

class UploadDetail(BaseModel):
    upload_id: UUID
    original_filename: str
    file_format: str
    file_size_bytes: int
    status: str
    page_count: Optional[int]
    phi_detected: Optional[bool]
    phi_purge_confirmed: Optional[bool]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    context: Optional[ContextRequest] = None

    model_config = {"from_attributes": True}
