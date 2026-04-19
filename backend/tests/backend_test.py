"""Backend API tests for CHC Pro AI.

Covers:
- Captcha + registration flow (OTP + MFA confirm)
- Login (admin, coder, pending user, lockout, wrong creds)
- Token refresh, /auth/me, change password
- Admin pending/approve/reject/audit
- Coding session create/upload/process + PHI purge + coding output
- Validation errors (weak password, bad NPI, bad EIN)
"""
import os
import re
import io
import time
import uuid
import pyotp
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hipaa-billing-ai.preview.emergentagent.com").rstrip("/")
# Fallback: read from frontend/.env
if "REACT_APP_BACKEND_URL" not in os.environ:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL"):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@chcpro.ai"
ADMIN_PASSWORD = "AdminPass@2025!"
CODER_EMAIL = "coder@chcpro.ai"
CODER_PASSWORD = "CoderPass@2025!"


# ---------------- helpers ----------------
def _solve_captcha():
    r = requests.get(f"{API}/captcha", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    q = body["question"]  # e.g. "4 + 7 = ?"
    m = re.match(r"\s*(\d+)\s*([+\-×])\s*(\d+)", q)
    assert m, q
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    ans = a + b if op == "+" else a - b if op == "-" else a * b
    return body["token"], str(ans)


def _unique_email(prefix="TEST_user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def _register_payload(email, password="StrongPass!2345"):
    tok, ans = _solve_captcha()
    return {
        "npi": "1234567890",
        "tax_id": "987654321",
        "email": email,
        "first_name": "Test",
        "middle_name": "",
        "last_name": "User",
        "date_of_birth": "1990-01-01",
        "security_question": "Favorite color?",
        "security_answer": "blue",
        "password": password,
        "verify_password": password,
        "captcha_token": tok,
        "captcha_answer": ans,
    }


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("mfa_required") is False
    assert "access_token" in data and "refresh_token" in data
    assert data["user"]["email"] == ADMIN_EMAIL
    assert data["user"]["role"] == "admin"
    return data["access_token"]


@pytest.fixture(scope="session")
def coder_token():
    r = requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": CODER_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Coder login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("mfa_required") is False
    assert data["user"]["role"] == "coder"
    assert data["user"]["approved"] is True
    return data["access_token"]


def auth_headers(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------------- Health ----------------
class TestHealth:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_captcha(self):
        tok, ans = _solve_captcha()
        assert tok and ans


# ---------------- Registration flow ----------------
class TestRegistrationFlow:
    state = {}

    def test_01_register(self):
        email = _unique_email()
        TestRegistrationFlow.state["email"] = email
        r = requests.post(f"{API}/auth/register", json=_register_payload(email), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "registration_token" in data and "dev_otp" in data
        assert len(data["dev_otp"]) == 6
        TestRegistrationFlow.state["reg_token"] = data["registration_token"]
        TestRegistrationFlow.state["otp"] = data["dev_otp"]

    def test_02_verify_otp(self):
        s = TestRegistrationFlow.state
        r = requests.post(f"{API}/auth/verify-otp", json={"registration_token": s["reg_token"], "otp": s["otp"]}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "mfa_secret" in data and "mfa_qr_png" in data and "otpauth_url" in data
        assert data["mfa_qr_png"].startswith("iVBOR") or len(data["mfa_qr_png"]) > 100  # base64 PNG
        s["reg_token2"] = data["registration_token"]
        s["mfa_secret"] = data["mfa_secret"]

    def test_03_confirm_mfa(self):
        s = TestRegistrationFlow.state
        code = pyotp.TOTP(s["mfa_secret"]).now()
        r = requests.post(f"{API}/auth/confirm-mfa", json={"registration_token": s["reg_token2"], "code": code}, timeout=20)
        assert r.status_code == 200, r.text
        assert "Awaiting" in r.json()["message"] or "complete" in r.json()["message"].lower()

    def test_04_pending_login_blocked(self):
        s = TestRegistrationFlow.state
        r = requests.post(f"{API}/auth/login", json={"email": s["email"], "password": "StrongPass!2345"}, timeout=20)
        assert r.status_code == 403
        assert "pending" in r.json()["detail"].lower()


# ---------------- Validation ----------------
class TestValidation:
    def test_weak_password(self):
        r = requests.post(f"{API}/auth/register", json=_register_payload(_unique_email(), password="short1A!"), timeout=20)
        assert r.status_code == 400

    def test_bad_npi(self):
        payload = _register_payload(_unique_email())
        payload["npi"] = "12345"  # too short
        r = requests.post(f"{API}/auth/register", json=payload, timeout=20)
        assert r.status_code == 400
        assert "NPI" in r.json()["detail"]

    def test_bad_ein(self):
        payload = _register_payload(_unique_email())
        payload["tax_id"] = "12"  # too short
        r = requests.post(f"{API}/auth/register", json=payload, timeout=20)
        assert r.status_code == 400
        assert "Tax" in r.json()["detail"] or "EIN" in r.json()["detail"]

    def test_bad_captcha(self):
        payload = _register_payload(_unique_email())
        payload["captcha_answer"] = "-999999"
        r = requests.post(f"{API}/auth/register", json=payload, timeout=20)
        assert r.status_code == 400


# ---------------- Admin ----------------
class TestAdmin:
    def test_me_admin(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=auth_headers(admin_token), timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL
        assert r.json()["role"] == "admin"

    def test_pending_list(self, admin_token):
        r = requests.get(f"{API}/admin/pending", headers=auth_headers(admin_token), timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_audit_log(self, admin_token):
        r = requests.get(f"{API}/admin/audit", headers=auth_headers(admin_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Ensure no raw PHI fields (we only log actions/meta)
        for entry in data[:5]:
            assert "action" in entry and "timestamp" in entry

    def test_approve_reject_flow(self, admin_token):
        # Create a pending user end-to-end (email is lower-cased server-side)
        email = _unique_email("TEST_approve").lower()
        reg = requests.post(f"{API}/auth/register", json=_register_payload(email), timeout=20).json()
        v = requests.post(f"{API}/auth/verify-otp", json={"registration_token": reg["registration_token"], "otp": reg["dev_otp"]}, timeout=20).json()
        code = pyotp.TOTP(v["mfa_secret"]).now()
        requests.post(f"{API}/auth/confirm-mfa", json={"registration_token": v["registration_token"], "code": code}, timeout=20)

        # Find user id in pending list
        pending = requests.get(f"{API}/admin/pending", headers=auth_headers(admin_token), timeout=15).json()
        target = next((u for u in pending if u["email"] == email), None)
        assert target, "User not in pending list"

        # Approve
        r = requests.post(f"{API}/admin/users/{target['id']}/approve", headers=auth_headers(admin_token), json={"reason": "ok"}, timeout=15)
        assert r.status_code == 200

        # User now cannot login WITHOUT MFA (they set MFA). Verify login returns mfa_required
        login = requests.post(f"{API}/auth/login", json={"email": email, "password": "StrongPass!2345"}, timeout=15)
        assert login.status_code == 200
        assert login.json().get("mfa_required") is True

        # Reject another newly created pending user
        email2 = _unique_email("TEST_reject").lower()
        reg2 = requests.post(f"{API}/auth/register", json=_register_payload(email2), timeout=20).json()
        v2 = requests.post(f"{API}/auth/verify-otp", json={"registration_token": reg2["registration_token"], "otp": reg2["dev_otp"]}, timeout=20).json()
        code2 = pyotp.TOTP(v2["mfa_secret"]).now()
        requests.post(f"{API}/auth/confirm-mfa", json={"registration_token": v2["registration_token"], "code": code2}, timeout=20)
        pending2 = requests.get(f"{API}/admin/pending", headers=auth_headers(admin_token), timeout=15).json()
        t2 = next((u for u in pending2 if u["email"] == email2), None)
        assert t2
        r = requests.post(f"{API}/admin/users/{t2['id']}/reject", headers=auth_headers(admin_token), json={"reason": "test"}, timeout=15)
        assert r.status_code == 200


# ---------------- Login edge cases ----------------
class TestLoginEdges:
    def test_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "WrongPass!2025"}, timeout=15)
        assert r.status_code == 401

    def test_lockout_after_5_fails(self):
        # Create a fresh approved user to test lockout without locking seeded admin
        # Simpler: use a random user who won't pass email_verified. But login only increments on password mismatch
        # so the check happens even for unverified accounts if password is wrong.
        email = _unique_email("TEST_lock")
        reg = requests.post(f"{API}/auth/register", json=_register_payload(email), timeout=20).json()
        # Now 5 bad password attempts
        for _ in range(5):
            requests.post(f"{API}/auth/login", json={"email": email, "password": "BadPass!23456"}, timeout=15)
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "BadPass!23456"}, timeout=15)
        assert r.status_code == 423, f"Expected 423 got {r.status_code}: {r.text}"

    def test_refresh_token(self):
        r = requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": CODER_PASSWORD}, timeout=15)
        refresh = r.json()["refresh_token"]
        r2 = requests.post(f"{API}/auth/refresh", json={"refresh_token": refresh}, timeout=15)
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    def test_lockout_reset_on_success(self):
        # 3 bad attempts on coder, then correct login should reset counter
        for _ in range(3):
            requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": "Wrong!12345X"}, timeout=15)
        r = requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": CODER_PASSWORD}, timeout=15)
        assert r.status_code == 200


# ---------------- Settings ----------------
class TestSettings:
    def test_change_password_wrong_current(self, coder_token):
        r = requests.post(f"{API}/settings/change-password",
                          headers=auth_headers(coder_token),
                          json={"current_password": "wrong", "new_password": "NewStrong!2345"}, timeout=15)
        assert r.status_code == 400

    def test_change_password_and_revert(self, coder_token):
        new_pw = "TempPass!2345"
        r = requests.post(f"{API}/settings/change-password",
                          headers=auth_headers(coder_token),
                          json={"current_password": CODER_PASSWORD, "new_password": new_pw}, timeout=15)
        assert r.status_code == 200, r.text
        # Confirm we can login with new
        r2 = requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": new_pw}, timeout=15)
        assert r2.status_code == 200
        # Revert
        tok2 = r2.json()["access_token"]
        r3 = requests.post(f"{API}/settings/change-password",
                           headers=auth_headers(tok2),
                           json={"current_password": new_pw, "new_password": CODER_PASSWORD}, timeout=15)
        assert r3.status_code == 200


# ---------------- Coding workflow ----------------
SAMPLE_MED_TEXT = (
    "Patient: John Smith DOB: 01/15/1960 SSN: 123-45-6789\n"
    "Diagnosed with pneumonia and hypertension.\n"
    "CBC and chest x-ray performed."
)


class TestCodingWorkflow:
    state = {}

    def test_create_session_invalid_claim(self, coder_token):
        r = requests.post(f"{API}/coding/sessions",
                          headers=auth_headers(coder_token),
                          json={"claim_type": "BAD", "payer": "MEDICARE"}, timeout=15)
        assert r.status_code == 400

    def test_create_session(self, coder_token):
        r = requests.post(f"{API}/coding/sessions",
                          headers=auth_headers(coder_token),
                          json={"claim_type": "CMS-1500", "codes_required": ["ALL"],
                                "specialty": ["Internal Medicine"], "payer": "MEDICARE"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["claim_type"] == "CMS-1500"
        assert data["payer"] == "MEDICARE"
        assert data["status"] == "created"
        assert "id" in data
        TestCodingWorkflow.state["session_id"] = data["id"]

    def test_upload_file(self, coder_token):
        sid = TestCodingWorkflow.state["session_id"]
        files = {"files": ("record.txt", io.BytesIO(SAMPLE_MED_TEXT.encode()), "text/plain")}
        r = requests.post(f"{API}/coding/sessions/{sid}/upload",
                          headers=auth_headers(coder_token),
                          files=files, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["session_id"] == sid
        assert len(data["files"]) == 1

    def test_process_session(self, coder_token):
        sid = TestCodingWorkflow.state["session_id"]
        r = requests.post(f"{API}/coding/sessions/{sid}/process",
                          headers=auth_headers(coder_token), timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "coding_result" in data
        assert "phi_report" in data
        result = data["coding_result"]

        # Verify PHI was found
        cats = data["phi_report"].get("categories_found", [])
        red = data["phi_report"].get("redactions", [])
        assert len(red) > 0, "No PHI redactions detected"
        # Expect name/ssn/dob like categories
        joined_cats = " ".join([str(c).lower() for c in cats])
        assert any(k in joined_cats for k in ["name", "ssn", "dob", "date"]), f"cats={cats}"

        # Verify expected codes appear somewhere in result (flatten)
        flat = str(result).lower()
        for code in ["j18.9", "i10", "85025", "71046"]:
            assert code.lower() in flat, f"Missing expected code {code} in result"

        # Principal diagnosis present
        assert result.get("principal_diagnosis") is not None

    def test_list_sessions_max2(self, coder_token):
        r = requests.get(f"{API}/coding/sessions", headers=auth_headers(coder_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    def test_get_session_detail(self, coder_token):
        sid = TestCodingWorkflow.state["session_id"]
        r = requests.get(f"{API}/coding/sessions/{sid}", headers=auth_headers(coder_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == sid
        assert data["status"] == "processed"

    def test_admin_can_also_code(self, admin_token):
        """admin has approved=True so require_approved_user should allow it."""
        r = requests.post(f"{API}/coding/sessions",
                          headers=auth_headers(admin_token),
                          json={"claim_type": "UB-04", "payer": "COMMERCIAL"}, timeout=15)
        assert r.status_code == 200, r.text
