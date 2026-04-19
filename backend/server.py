"""CHC Pro AI - FastAPI server.

HIPAA-aware medical coding backend. All processing (OCR, PHI purge, coding)
runs in-process with no external AI calls.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os  # noqa: E402
import uuid  # noqa: E402
import secrets  # noqa: E402
import logging  # noqa: E402
import asyncio  # noqa: E402
from datetime import datetime, timezone, timedelta  # noqa: E402
from typing import List, Optional  # noqa: E402

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, UploadFile, File, Form  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from pydantic import BaseModel, EmailStr, Field  # noqa: E402

from auth_utils import (  # noqa: E402
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_mfa_challenge_token,
    create_registration_token,
    decode_token,
    new_totp_secret,
    totp_provisioning_uri,
    verify_totp,
    qr_png_base64,
    generate_otp,
    valid_password,
    valid_npi,
    valid_ein,
)
from phi_purger import purge_phi  # noqa: E402
from ocr_service import extract_text  # noqa: E402
from coding_engine import run_coding, coding_to_dict  # noqa: E402

# ---------- DB ----------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# ---------- App ----------
app = FastAPI(title="CHC Pro AI")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("chcpro")

SESSION_RETENTION_HOURS = int(os.environ.get("SESSION_RETENTION_HOURS", "24"))


# ---------- Helpers ----------

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def audit(user_id: Optional[str], action: str, meta: Optional[dict] = None) -> None:
    """Append an audit-log entry. Never logs PHI."""
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "meta": meta or {},
        "timestamp": iso_now(),
    })


async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth[7:]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0, "mfa_secret": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_approved_user(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("approved"):
        raise HTTPException(status_code=403, detail="Account pending approval")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in {"admin", "provider"}:
        raise HTTPException(status_code=403, detail="Admin or Provider role required")
    return user


# ---------- Schemas ----------

class RegisterIn(BaseModel):
    npi: str
    tax_id: str
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    date_of_birth: str  # ISO date yyyy-mm-dd
    security_question: str
    security_answer: str
    password: str
    verify_password: str
    captcha_token: str
    captcha_answer: str


class VerifyOtpIn(BaseModel):
    registration_token: str
    otp: str


class ConfirmMFAIn(BaseModel):
    registration_token: str
    code: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MFAVerifyIn(BaseModel):
    mfa_token: str
    code: str


class SessionCreateIn(BaseModel):
    claim_type: str  # UB-04 | CMS-1500
    codes_required: List[str] = Field(default_factory=lambda: ["ALL"])
    specialty: List[str] = Field(default_factory=list)
    payer: str  # MEDICARE | MEDICAID | COMMERCIAL
    state: Optional[str] = None


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class ResetMFAIn(BaseModel):
    password: str


class ApprovalIn(BaseModel):
    reason: Optional[str] = ""


# ---------- Captcha (local, no 3rd-party) ----------
# Generate arithmetic challenges server-side; client submits the answer.
_captchas: dict[str, int] = {}


@api.get("/captcha")
async def get_captcha():
    a = secrets.randbelow(9) + 1
    b = secrets.randbelow(9) + 1
    op = secrets.choice(["+", "-", "×"])
    if op == "+":
        answer = a + b
    elif op == "-":
        # avoid negative
        if b > a:
            a, b = b, a
        answer = a - b
    else:
        answer = a * b
    token = secrets.token_urlsafe(16)
    _captchas[token] = answer
    # Limit size
    if len(_captchas) > 1000:
        _captchas.clear()
    return {"token": token, "question": f"{a} {op} {b} = ?"}


def _check_captcha(token: str, answer: str) -> bool:
    expected = _captchas.pop(token, None)
    if expected is None:
        return False
    try:
        return int(str(answer).strip()) == expected
    except Exception:
        return False


# ---------- Auth ----------

@api.post("/auth/register")
async def register(data: RegisterIn):
    if not _check_captcha(data.captcha_token, data.captcha_answer):
        raise HTTPException(status_code=400, detail="CAPTCHA verification failed")

    if data.password != data.verify_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    ok, msg = valid_password(data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    if not valid_npi(data.npi):
        raise HTTPException(status_code=400, detail="Invalid NPI: must be 10 digits")
    if not valid_ein(data.tax_id):
        raise HTTPException(status_code=400, detail="Invalid Tax ID/EIN: must be 9 digits")

    try:
        dob = datetime.strptime(data.date_of_birth, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date of birth")
    today = datetime.now(timezone.utc).date()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:
        raise HTTPException(status_code=400, detail="User must be 18+")

    email = str(data.email).lower()
    existing = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    otp = generate_otp(6)
    user_doc = {
        "id": user_id,
        "email": email,
        "first_name": data.first_name.strip(),
        "middle_name": (data.middle_name or "").strip(),
        "last_name": data.last_name.strip(),
        "npi": data.npi,
        "tax_id": data.tax_id,
        "date_of_birth": data.date_of_birth,
        "security_question": data.security_question,
        "security_answer_hash": hash_password(data.security_answer.lower().strip()),
        "password_hash": hash_password(data.password),
        "role": "coder",
        "approved": False,
        "email_verified": False,
        "mfa_enabled": False,
        "mfa_secret": None,
        "pending_otp": otp,
        "pending_otp_expires": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "failed_login_attempts": 0,
        "locked_until": None,
        "created_at": iso_now(),
    }
    await db.users.insert_one(user_doc)
    await audit(user_id, "register_submit", {"email": email})
    logger.info("OTP for %s (dev mode): %s", email, otp)

    reg_token = create_registration_token(user_id, "otp")
    # Dev mode: return OTP in response so it can be displayed on-screen.
    return {
        "registration_token": reg_token,
        "message": "OTP sent to your email (dev mode: OTP is shown on screen).",
        "dev_otp": otp,
    }


@api.post("/auth/verify-otp")
async def verify_otp(data: VerifyOtpIn):
    try:
        payload = decode_token(data.registration_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid registration token")
    if payload.get("type") != "registration" or payload.get("stage") != "otp":
        raise HTTPException(status_code=400, detail="Wrong registration stage")
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")

    expires = user.get("pending_otp_expires")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired — please register again")
    if str(data.otp).strip() != str(user.get("pending_otp")):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    secret = new_totp_secret()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "email_verified": True,
            "pending_otp": None,
            "pending_otp_expires": None,
            "mfa_secret": secret,
            "mfa_enabled": False,
        }},
    )
    await audit(user["id"], "email_verified")

    uri = totp_provisioning_uri(secret, user["email"])
    qr = qr_png_base64(uri)
    reg_token = create_registration_token(user["id"], "mfa")
    return {
        "registration_token": reg_token,
        "mfa_secret": secret,
        "mfa_qr_png": qr,
        "otpauth_url": uri,
    }


@api.post("/auth/confirm-mfa")
async def confirm_mfa(data: ConfirmMFAIn):
    try:
        payload = decode_token(data.registration_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid registration token")
    if payload.get("type") != "registration" or payload.get("stage") != "mfa":
        raise HTTPException(status_code=400, detail="Wrong registration stage")
    user = await db.users.find_one({"id": payload["sub"]})
    if not user or not user.get("mfa_secret"):
        raise HTTPException(status_code=400, detail="MFA not initialized")
    if not verify_totp(user["mfa_secret"], data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    await db.users.update_one({"id": user["id"]}, {"$set": {"mfa_enabled": True}})
    await audit(user["id"], "mfa_enabled")

    # Notify any admin (in-app log). Email would be sent in production.
    admins = await db.users.find({"role": {"$in": ["admin", "provider"]}}, {"id": 1, "_id": 0}).to_list(50)
    for a in admins:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": a["id"],
            "kind": "approval_request",
            "title": "New user awaiting approval",
            "body": f"A new user ({user['email']}) has completed registration and is pending approval.",
            "read": False,
            "created_at": iso_now(),
        })

    return {"message": "Registration complete. Awaiting admin approval."}


@api.post("/auth/login")
async def login(data: LoginIn):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Lockout
    locked = user.get("locked_until")
    if locked and datetime.fromisoformat(locked) > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Account locked. Try again later or contact admin.")

    if not verify_password(data.password, user.get("password_hash", "")):
        attempts = (user.get("failed_login_attempts") or 0) + 1
        updates: dict = {"failed_login_attempts": attempts}
        if attempts >= 5:
            updates["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
        await audit(user["id"], "login_failed", {"attempts": attempts})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("email_verified"):
        raise HTTPException(status_code=403, detail="Email not verified. Complete registration first.")

    if not user.get("approved"):
        raise HTTPException(status_code=403, detail="Account pending approval from your Provider/Administrator")

    # Reset failed attempts
    await db.users.update_one({"id": user["id"]}, {"$set": {"failed_login_attempts": 0, "locked_until": None}})

    if user.get("mfa_enabled"):
        token = create_mfa_challenge_token(user["id"])
        await audit(user["id"], "login_password_ok")
        return {"mfa_required": True, "mfa_token": token}

    # No MFA (e.g., admin bootstrap) — issue tokens directly
    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])
    await audit(user["id"], "login_success")
    return {
        "mfa_required": False,
        "access_token": access,
        "refresh_token": refresh,
        "user": _public_user(user),
    }


@api.post("/auth/login-mfa")
async def login_mfa(data: MFAVerifyIn):
    try:
        payload = decode_token(data.mfa_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid MFA token")
    if payload.get("type") != "mfa_challenge":
        raise HTTPException(status_code=401, detail="Wrong token type")
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not verify_totp(user.get("mfa_secret", ""), data.code):
        await audit(user["id"], "mfa_failed")
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])
    await audit(user["id"], "login_success")
    return {"access_token": access, "refresh_token": refresh, "user": _public_user(user)}


@api.post("/auth/refresh")
async def refresh_token(request: Request):
    body = await request.json()
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user["id"], user["email"], user["role"])
    return {"access_token": access}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return _public_user(user)


@api.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    await audit(user["id"], "logout")
    return {"message": "Logged out"}


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "middle_name": user.get("middle_name", ""),
        "role": user.get("role", "coder"),
        "approved": user.get("approved", False),
        "email_verified": user.get("email_verified", False),
        "mfa_enabled": user.get("mfa_enabled", False),
        "npi": user.get("npi", ""),
        "facility_name": user.get("facility_name", "CHC Provider Group"),
        "security_question": user.get("security_question", ""),
    }


# ---------- Admin ----------

@api.get("/admin/pending")
async def admin_pending(admin: dict = Depends(require_admin)):
    users = await db.users.find(
        {"approved": False, "email_verified": True, "role": "coder"},
        {"_id": 0, "password_hash": 0, "mfa_secret": 0, "security_answer_hash": 0},
    ).to_list(500)
    return users


@api.get("/admin/users")
async def admin_users(admin: dict = Depends(require_admin)):
    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0, "mfa_secret": 0, "security_answer_hash": 0, "pending_otp": 0},
    ).to_list(1000)
    return users


@api.post("/admin/users/{user_id}/approve")
async def admin_approve(user_id: str, data: ApprovalIn, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"id": user_id}, {"$set": {"approved": True, "approved_at": iso_now(), "approved_by": admin["id"]}})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "kind": "approval_result",
        "title": "Your account has been approved",
        "body": "You can now log in to CHC Pro AI.",
        "read": False,
        "created_at": iso_now(),
    })
    await audit(admin["id"], "admin_approve_user", {"target_user": user_id})
    return {"message": "User approved"}


@api.post("/admin/users/{user_id}/reject")
async def admin_reject(user_id: str, data: ApprovalIn, admin: dict = Depends(require_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"id": user_id}, {"$set": {"approved": False, "rejected_reason": data.reason, "rejected_at": iso_now()}})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "kind": "approval_result",
        "title": "Your account was rejected",
        "body": f"Reason: {data.reason or 'Not specified'}",
        "read": False,
        "created_at": iso_now(),
    })
    await audit(admin["id"], "admin_reject_user", {"target_user": user_id, "reason": data.reason})
    return {"message": "User rejected"}


@api.post("/admin/users/{user_id}/suspend")
async def admin_suspend(user_id: str, admin: dict = Depends(require_admin)):
    await db.users.update_one({"id": user_id}, {"$set": {"approved": False, "suspended": True}})
    await audit(admin["id"], "admin_suspend_user", {"target_user": user_id})
    return {"message": "User suspended"}


@api.get("/admin/audit")
async def admin_audit(admin: dict = Depends(require_admin), limit: int = 200):
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs


# ---------- Coding workflow ----------

MAX_UPLOAD_SIZE = 15 * 1024 * 1024  # 15 MB per file
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".docx", ".txt"}


@api.post("/coding/sessions")
async def create_session(data: SessionCreateIn, user: dict = Depends(require_approved_user)):
    if data.claim_type not in {"UB-04", "CMS-1500"}:
        raise HTTPException(status_code=400, detail="claim_type must be UB-04 or CMS-1500")
    if data.payer not in {"MEDICARE", "MEDICAID", "COMMERCIAL"}:
        raise HTTPException(status_code=400, detail="Invalid payer")
    if data.payer == "MEDICAID" and not data.state:
        raise HTTPException(status_code=400, detail="State is required for Medicaid")

    # Enforce business rule: keep at most 2 active sessions per user in history.
    await _enforce_session_cap(user["id"])

    session = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "claim_type": data.claim_type,
        "codes_required": data.codes_required or ["ALL"],
        "specialty": data.specialty,
        "payer": data.payer,
        "state": data.state,
        "files": [],
        "status": "created",
        "ocr_text_length": 0,
        "phi_report": {},
        "coding_result": None,
        "created_at": iso_now(),
    }
    await db.coding_sessions.insert_one(session)
    await audit(user["id"], "session_create", {"session_id": session["id"], "claim_type": data.claim_type, "payer": data.payer})
    session.pop("_id", None)
    return session


async def _enforce_session_cap(user_id: str) -> None:
    # Business rule: history shows max 2 previous sessions; purge older ones.
    sessions = await db.coding_sessions.find({"user_id": user_id}, {"_id": 0, "id": 1, "created_at": 1}).sort("created_at", -1).to_list(100)
    keep = {s["id"] for s in sessions[:2]}
    to_remove = [s["id"] for s in sessions if s["id"] not in keep]
    if to_remove:
        await db.coding_sessions.delete_many({"id": {"$in": to_remove}})


@api.post("/coding/sessions/{session_id}/upload")
async def upload_files(session_id: str, files: List[UploadFile] = File(...), user: dict = Depends(require_approved_user)):
    session = await db.coding_sessions.find_one({"id": session_id, "user_id": user["id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    uploaded: List[dict] = []
    combined_bytes: List[tuple[str, bytes]] = []
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        data = await f.read()
        if len(data) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large (>{MAX_UPLOAD_SIZE // (1024*1024)} MB)")
        combined_bytes.append((f.filename or "upload", data))
        uploaded.append({"filename": f.filename, "size": len(data), "ext": ext})

    # Store raw bytes temporarily inside the session document (encrypted-at-rest
    # by MongoDB volume). These are purged once processing completes or after 24h.
    await db.coding_sessions.update_one(
        {"id": session_id},
        {"$set": {
            "files": uploaded,
            "status": "uploaded",
            "uploaded_at": iso_now(),
        }},
    )
    # Keep bytes in a separate collection to avoid bloating the main session doc.
    await db.session_files.delete_many({"session_id": session_id})
    for name, data in combined_bytes:
        await db.session_files.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "filename": name,
            "data": data,
            "created_at": iso_now(),
        })

    await audit(user["id"], "files_uploaded", {"session_id": session_id, "count": len(uploaded)})
    return {"session_id": session_id, "files": uploaded}


@api.post("/coding/sessions/{session_id}/process")
async def process_session(session_id: str, user: dict = Depends(require_approved_user)):
    session = await db.coding_sessions.find_one({"id": session_id, "user_id": user["id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] not in {"uploaded", "processed"}:
        raise HTTPException(status_code=400, detail="Session not ready for processing")

    files = await db.session_files.find({"session_id": session_id}, {"_id": 0}).to_list(50)
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Step A: OCR
    ocr_texts: List[str] = []
    total_pages = 0
    for f in files:
        text, pages = extract_text(f["filename"], f["data"])
        ocr_texts.append(f"\n--- FILE: {f['filename']} ---\n{text}")
        total_pages += pages

    raw_text = "\n".join(ocr_texts)

    # Step B: PHI purging (internal, no external AI)
    deidentified, report = purge_phi(raw_text)

    # Step C: Internal coding
    result = run_coding(
        deidentified,
        session_id=session_id,
        claim_type=session["claim_type"],
        codes_required=session["codes_required"],
        specialty=session["specialty"],
        payer=session["payer"],
        state=session.get("state"),
    )
    result_dict = coding_to_dict(result)

    # Discard raw file bytes once processing completes (PHI minimization)
    await db.session_files.delete_many({"session_id": session_id})

    await db.coding_sessions.update_one(
        {"id": session_id},
        {"$set": {
            "status": "processed",
            "ocr_text_length": len(raw_text),
            "ocr_pages": total_pages,
            "phi_report": {"redactions": report.redactions, "categories_found": report.categories_found},
            "coding_result": result_dict,
            "processed_at": iso_now(),
        }},
    )
    await audit(user["id"], "session_processed", {"session_id": session_id, "pages": total_pages})

    return {
        "session_id": session_id,
        "phi_report": {"redactions": report.redactions, "categories_found": report.categories_found},
        "ocr_pages": total_pages,
        "coding_result": result_dict,
    }


@api.get("/coding/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(require_approved_user)):
    session = await db.coding_sessions.find_one({"id": session_id, "user_id": user["id"]}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@api.get("/coding/sessions")
async def list_sessions(user: dict = Depends(require_approved_user)):
    # Enforce 24-hour retention at read time
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=SESSION_RETENTION_HOURS)).isoformat()
    await db.coding_sessions.delete_many({"user_id": user["id"], "created_at": {"$lt": cutoff}})
    sessions = await db.coding_sessions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(2)
    return sessions


@api.delete("/coding/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(require_approved_user)):
    await db.coding_sessions.delete_one({"id": session_id, "user_id": user["id"]})
    await db.session_files.delete_many({"session_id": session_id})
    await audit(user["id"], "session_delete", {"session_id": session_id})
    return {"message": "Session deleted"}


# ---------- Settings ----------

@api.post("/settings/change-password")
async def change_password(data: ChangePasswordIn, user: dict = Depends(get_current_user)):
    full = await db.users.find_one({"id": user["id"]})
    if not full or not verify_password(data.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    ok, msg = valid_password(data.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(data.new_password)}})
    await audit(user["id"], "password_changed")
    return {"message": "Password updated"}


@api.post("/settings/reset-mfa")
async def reset_mfa(data: ResetMFAIn, user: dict = Depends(get_current_user)):
    full = await db.users.find_one({"id": user["id"]})
    if not full or not verify_password(data.password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    secret = new_totp_secret()
    await db.users.update_one({"id": user["id"]}, {"$set": {"mfa_secret": secret, "mfa_enabled": False}})
    uri = totp_provisioning_uri(secret, full["email"])
    await audit(user["id"], "mfa_reset")
    return {"mfa_secret": secret, "mfa_qr_png": qr_png_base64(uri), "otpauth_url": uri}


@api.post("/settings/confirm-mfa-reset")
async def confirm_mfa_reset(data: ConfirmMFAIn, user: dict = Depends(get_current_user)):
    # reuse schema; registration_token here is unused — but we keep same shape
    full = await db.users.find_one({"id": user["id"]})
    if not full or not verify_totp(full.get("mfa_secret", ""), data.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    await db.users.update_one({"id": user["id"]}, {"$set": {"mfa_enabled": True}})
    await audit(user["id"], "mfa_reset_confirmed")
    return {"message": "MFA re-enabled"}


@api.get("/notifications")
async def list_notifications(user: dict = Depends(get_current_user)):
    notifs = await db.notifications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return notifs


# ---------- Root ----------

@api.get("/")
async def root():
    return {"app": "CHC Pro AI", "status": "ok", "time": iso_now()}


# ---------- Startup ----------

async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@chcpro.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "AdminPass@2025!")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "first_name": "System",
            "last_name": "Administrator",
            "npi": "0000000000",
            "tax_id": "000000000",
            "date_of_birth": "1980-01-01",
            "role": "admin",
            "approved": True,
            "email_verified": True,
            "mfa_enabled": False,
            "mfa_secret": None,
            "password_hash": hash_password(admin_password),
            "security_question": "seed",
            "security_answer_hash": hash_password("seed"),
            "facility_name": "CHC Pro AI Operations",
            "created_at": iso_now(),
        })
        logger.info("Seeded admin account: %s", admin_email)
    else:
        # Keep password in sync with env value (dev convenience)
        if not verify_password(admin_password, existing.get("password_hash", "")):
            await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password), "approved": True, "email_verified": True}})

    test_email = os.environ.get("TEST_USER_EMAIL", "coder@chcpro.ai")
    test_password = os.environ.get("TEST_USER_PASSWORD", "CoderPass@2025!")
    existing_test = await db.users.find_one({"email": test_email})
    if not existing_test:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": test_email,
            "first_name": "Test",
            "last_name": "Coder",
            "npi": "1234567890",
            "tax_id": "123456789",
            "date_of_birth": "1985-06-15",
            "role": "coder",
            "approved": True,
            "email_verified": True,
            "mfa_enabled": False,
            "mfa_secret": None,
            "password_hash": hash_password(test_password),
            "security_question": "What is your favorite color?",
            "security_answer_hash": hash_password("blue"),
            "facility_name": "CHC Demo Facility",
            "created_at": iso_now(),
        })
        logger.info("Seeded test coder account: %s", test_email)
    else:
        if not verify_password(test_password, existing_test.get("password_hash", "")):
            await db.users.update_one({"email": test_email}, {"$set": {"password_hash": hash_password(test_password), "approved": True, "email_verified": True}})


async def purge_old_sessions_loop():
    while True:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=SESSION_RETENTION_HOURS)).isoformat()
            res = await db.coding_sessions.delete_many({"created_at": {"$lt": cutoff}})
            if res.deleted_count:
                logger.info("Auto-purged %s expired coding sessions", res.deleted_count)
            # Cleanup orphan session_files too
            orphans = await db.session_files.find({"created_at": {"$lt": cutoff}}, {"_id": 0, "session_id": 1}).to_list(500)
            if orphans:
                await db.session_files.delete_many({"created_at": {"$lt": cutoff}})
        except Exception as e:
            logger.warning("purge loop error: %s", e)
        await asyncio.sleep(3600)  # hourly


@app.on_event("startup")
async def on_start():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.coding_sessions.create_index("user_id")
    await db.coding_sessions.create_index("created_at")
    await db.audit_logs.create_index("timestamp")
    await db.session_files.create_index("session_id")
    await seed_admin()
    asyncio.create_task(purge_old_sessions_loop())


@app.on_event("shutdown")
async def on_stop():
    client.close()


# Error handlers
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
