"""
CHC Pro AI — Registration Routes
POST /api/v1/auth/register/step1              Basic info
POST /api/v1/auth/register/step2/verify-npi   NPI + OIG + PECOS
POST /api/v1/auth/register/step3/send-otp     Send 6-digit OTP
POST /api/v1/auth/register/step3/verify-otp   Verify OTP
POST /api/v1/auth/register/step4/set-password Password setup
POST /api/v1/auth/register/step4/setup-2fa    Generate QR code
POST /api/v1/auth/register/step4/verify-2fa   Confirm first TOTP
POST /api/v1/auth/register/step5/esignature   Sign + create Cognito user
"""
import logging
from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.auth_schemas import (
    ESignatureRequest, ESignatureResponse,
    RegStep1Request, RegStep1Response,
    RegStep2Request, RegStep2Response,
    SendOTPRequest, SendOTPResponse,
    Setup2FAResponse, SetPasswordRequest,
    VerifyOTPRequest, VerifyOTPResponse,
    Verify2FARequest,
)
from app.services.cognito_service import cognito, CognitoError
from app.services.esignature_service import store_signature, ESignatureError
from app.services.npi_service import check_oig, check_pecos, verify_npi, NPIError, OIGExcludedError
from app.services.otp_service import (
    generate_otp, new_totp_secret, send_otp_email, send_otp_sms,
    session_create, session_delete, session_get, session_update,
    totp_qr_base64, verify_otp, verify_totp,
    OTPDeliveryError, OTPExpiredError, OTPInvalidError, OTPRateLimitError,
    SessionExpiredError,
)
from config import get_settings

log      = logging.getLogger(__name__)
settings = get_settings()

router  = APIRouter(prefix="/api/v1/auth/register", tags=["Registration"])
limiter = Limiter(key_func=get_remote_address)


def _guard(session: dict | None) -> dict:
    if not session:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Registration session expired. Please start again from step 1."
        )
    return session


def _client_info(request: Request) -> tuple[str, str]:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    return ip, ua


# ── Step 1: Basic info ─────────────────────────────────────────────────────

@router.post("/step1", response_model=RegStep1Response)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def step1_basic_info(request: Request, body: RegStep1Request):
    if cognito.user_exists(body.email):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An account with this email already exists. Please log in instead."
        )

    token = await session_create(body.email, {
        "step":          1,
        "first_name":    body.first_name,
        "last_name":     body.last_name,
        "email":         body.email,
        "phone":         body.phone,
        "organization":  body.organization,
        "provider_type": body.provider_type,
        "specialty":     body.specialty,
        "state":         body.state,
    })

    return RegStep1Response(
        session_token=token,
        message="Step 1 complete. Please enter your NPI to continue.",
    )


# ── Step 2: NPI + OIG + PECOS ──────────────────────────────────────────────

@router.post("/step2/verify-npi", response_model=RegStep2Response)
@limiter.limit("5/minute")
async def step2_verify_npi(request: Request, body: RegStep2Request):
    session = _guard(await session_get(body.session_token))

    try:
        npi_detail = await verify_npi(body.npi, body.entity_type)
    except NPIError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))

    try:
        oig_clear = await check_oig(
            session["first_name"], session["last_name"], body.npi
        )
    except OIGExcludedError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

    pecos_enrolled = await check_pecos(body.npi)

    await session_update(body.session_token, {
        "step":              2,
        "npi":               body.npi,
        "tax_id_last4":      body.tax_id[-4:],
        "entity_type":       body.entity_type,
        "npi_provider_name": npi_detail.provider_name,
        "pecos_enrolled":    pecos_enrolled,
        "oig_clear":         oig_clear,
    })

    pecos_msg = "Medicare enrollment confirmed. " if pecos_enrolled else (
        "NPI not found in PECOS — you may need to enroll in Medicare separately. "
    )

    return RegStep2Response(
        session_token=body.session_token,
        npi_verified=True,
        oig_clear=oig_clear,
        pecos_enrolled=pecos_enrolled,
        npi_detail=npi_detail,
        message=f"NPI verified successfully. {pecos_msg}Next: verify your email.",
    )


# ── Step 3: OTP ────────────────────────────────────────────────────────────

@router.post("/step3/send-otp", response_model=SendOTPResponse)
@limiter.limit(settings.RATE_LIMIT_OTP)
async def step3_send_otp(request: Request, body: SendOTPRequest):
    session = _guard(await session_get(body.session_token))

    try:
        otp = await generate_otp(session["email"])
    except OTPRateLimitError as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e))

    try:
        if body.channel == "email":
            await send_otp_email(session["email"], session["first_name"], otp)
        else:
            await send_otp_sms(session["phone"], otp)
    except OTPDeliveryError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))

    return SendOTPResponse(
        message=f"A 6-digit verification code has been sent to your {body.channel}.",
        expires_in=settings.OTP_EXPIRE_SECONDS,
        channel=body.channel,
    )


@router.post("/step3/verify-otp", response_model=VerifyOTPResponse)
@limiter.limit("5/minute")
async def step3_verify_otp(request: Request, body: VerifyOTPRequest):
    session = _guard(await session_get(body.session_token))

    try:
        await verify_otp(session["email"], body.otp_code)
    except OTPExpiredError as e:
        raise HTTPException(status.HTTP_410_GONE, str(e))
    except OTPInvalidError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    await session_update(body.session_token, {"step": 3, "email_verified": True})

    return VerifyOTPResponse(
        session_token=body.session_token,
        verified=True,
        message="Email verified. Please set your password.",
    )


# ── Step 4a: Password ──────────────────────────────────────────────────────

@router.post("/step4/set-password")
@limiter.limit("5/minute")
async def step4_set_password(request: Request, body: SetPasswordRequest):
    session = _guard(await session_get(body.session_token))

    if not session.get("email_verified"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Email must be verified before setting a password. Please complete step 3."
        )

    # Store password temporarily — committed to Cognito at step 5
    await session_update(body.session_token, {
        "step": "4a", "_pwd_tmp": body.password
    })

    return {
        "message":       "Password set. Please configure your two-factor authentication.",
        "session_token": body.session_token,
    }


# ── Step 4b: 2FA Setup ─────────────────────────────────────────────────────

@router.post("/step4/setup-2fa", response_model=Setup2FAResponse)
async def step4_setup_2fa(request: Request, session_token: str):
    session = _guard(await session_get(session_token))

    secret = new_totp_secret()
    qr     = totp_qr_base64(session["email"], secret)

    await session_update(session_token, {"totp_secret": secret})

    return Setup2FAResponse(
        totp_secret=secret,
        qr_code_url=qr,
        manual_key=secret,
        message=(
            "Scan the QR code with Google Authenticator, Authy, or any TOTP app. "
            "Then enter the 6-digit code shown in your app to confirm setup."
        ),
    )


@router.post("/step4/verify-2fa")
@limiter.limit("5/minute")
async def step4_verify_2fa(request: Request, body: Verify2FARequest):
    session = _guard(await session_get(body.session_token))

    secret = session.get("totp_secret")
    if not secret:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "2FA not configured yet. Please complete step 4b first."
        )

    if not verify_totp(secret, body.totp_code):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "That code is incorrect. Check your authenticator app and try again. "
            "Codes refresh every 30 seconds."
        )

    await session_update(body.session_token, {"step": "4b", "2fa_confirmed": True})

    return {
        "message":       "Two-factor authentication configured. Please sign the agreements to complete registration.",
        "session_token": body.session_token,
    }


# ── Step 5: E-Signature + atomic Cognito user creation ────────────────────

@router.post("/step5/esignature", response_model=ESignatureResponse)
@limiter.limit("3/minute")
async def step5_esignature(request: Request, body: ESignatureRequest):
    session = _guard(await session_get(body.session_token))

    # Guard all prior steps
    if not session.get("email_verified"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Step 3 (email verification) not complete.")
    if not session.get("_pwd_tmp"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Step 4a (password) not complete.")
    if not session.get("2fa_confirmed"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Step 4b (2FA setup) not complete.")

    email       = session["email"]
    password    = session["_pwd_tmp"]
    totp_secret = session["totp_secret"]
    ip, ua      = _client_info(request)

    # ── Atomic user creation ──────────────────────────────────

    user_id = None
    try:
        user_id = cognito.create_user(
            email=email,
            temp_password=password + "_Tmp1!",
            attrs={
                "given_name":           session["first_name"],
                "family_name":          session["last_name"],
                "phone_number":         f"+1{session['phone']}",
                "custom:npi":           session.get("npi", ""),
                "custom:specialty":     session.get("specialty", ""),
                "custom:state":         session.get("state", ""),
                "custom:provider_type": session.get("provider_type", "individual"),
                "custom:pecos":         str(session.get("pecos_enrolled", False)),
                "custom:mfa_enabled":   "true",
                "custom:totp_secret":   totp_secret,
            },
        )
    except CognitoError as e:
        code = status.HTTP_409_CONFLICT if e.code == "DUPLICATE_EMAIL" else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(code, e.message)

    try:
        cognito.set_permanent_password(email, password)
    except CognitoError as e:
        cognito.delete_user(email)  # Rollback
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"Account creation failed at password step. Please try again.")

    try:
        cognito.enable_mfa(email)
    except CognitoError as e:
        log.warning(f"MFA enable failed for {email}: {e.message} — user still created")

    # ── Store e-signature ──────────────────────────────────────

    try:
        sig = await store_signature(
            user_id=user_id,
            email=email,
            full_legal_name=body.full_legal_name,
            signature_b64=body.signature_data,
            agreements={
                "terms":     body.agreed_to_terms,
                "hipaa_baa": body.agreed_to_hipaa_baa,
                "privacy":   body.agreed_to_privacy,
            },
            ip_address=ip,
            user_agent=ua,
        )
    except ESignatureError as e:
        cognito.delete_user(email)  # Rollback
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

    # Store sig reference in Cognito
    cognito.update_attributes(email, {
        "custom:sig_id": sig["signature_id"],
        "custom:sig_at": sig["signed_at"],
    })

    # ── Cleanup ────────────────────────────────────────────────
    await session_delete(body.session_token)

    log.info(f"Registration complete: {email} (user_id={user_id})")

    return ESignatureResponse(
        user_id=user_id,
        registration_complete=True,
        message=(
            "Registration complete! Your account is ready. "
            "Please log in with your email, password, and authenticator app."
        ),
    )
