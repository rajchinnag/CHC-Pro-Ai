"""Phase 2 backend tests for CHC Pro AI.

Covers new surface area only:
- /api/captcha returns recaptcha_v2 mode when RECAPTCHA_SECRET_KEY is configured
- /api/auth/register rejects invalid recaptcha tokens with 400
- Admin + Coder login still works (captcha only on register)
- /api/cms/status and /api/cms/refresh (auth + role gating)
- /api/coding/sessions/{id}/pdf (happy, unprocessed, unauthenticated)
- Expanded ICD-10-CM and CPT dictionary coverage
- Admin approve still sends email (no 500)
- CORS on preflight returns configured origin, not wildcard
"""
import os
import io
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hipaa-billing-ai.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@chcpro.ai"
ADMIN_PASSWORD = "AdminPass@2025!"
CODER_EMAIL = "coder@chcpro.ai"
CODER_PASSWORD = "CoderPass@2025!"

ALLOWED_ORIGIN = "https://hipaa-billing-ai.preview.emergentagent.com"


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    # Admin has mfa disabled — returns access_token directly
    assert data.get("mfa_required") is False
    tok = data.get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def coder_token() -> str:
    r = requests.post(f"{API}/auth/login", json={"email": CODER_EMAIL, "password": CODER_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Coder login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("mfa_required") is False
    tok = data.get("access_token")
    assert tok
    return tok


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


# ---------- Captcha ----------

class TestCaptcha:
    def test_captcha_returns_recaptcha_mode(self):
        r = requests.get(f"{API}/captcha", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("mode") == "recaptcha_v2", f"Expected recaptcha_v2 mode, got {data}"
        assert "site_key_hint" in data


# ---------- Register with invalid reCAPTCHA ----------

class TestRegisterInvalidRecaptcha:
    def test_register_invalid_recaptcha_returns_400(self):
        payload = {
            "npi": "1234567890",
            "tax_id": "123456789",
            "email": "TEST_bad_captcha@example.com",
            "first_name": "Bad",
            "last_name": "Captcha",
            "date_of_birth": "1990-01-01",
            "security_question": "color",
            "security_answer": "blue",
            "password": "StrongPass@2025!",
            "verify_password": "StrongPass@2025!",
            "captcha_token": "invalid_token_abc",
            "captcha_answer": "",
        }
        r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        body = r.json()
        detail = body.get("detail", "")
        assert "CAPTCHA" in detail or "captcha" in detail.lower(), f"Unexpected detail: {detail}"


# ---------- Login still works for seeded accounts ----------

class TestSeededLogin:
    def test_admin_login(self, admin_token):
        # Validated via fixture; also call /auth/me to verify token
        r = requests.get(f"{API}/auth/me", headers=_auth(admin_token), timeout=10)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == ADMIN_EMAIL
        assert me["role"] == "admin"

    def test_coder_login(self, coder_token):
        r = requests.get(f"{API}/auth/me", headers=_auth(coder_token), timeout=10)
        assert r.status_code == 200
        me = r.json()
        assert me["email"] == CODER_EMAIL
        assert me["role"] == "coder"


# ---------- CMS status & refresh ----------

class TestCMS:
    def test_cms_status_authenticated(self, coder_token):
        r = requests.get(f"{API}/cms/status", headers=_auth(coder_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "refreshed_at" in data
        assert "datasets" in data
        assert isinstance(data["datasets"], list)

    def test_cms_refresh_non_admin_forbidden(self, coder_token):
        r = requests.post(f"{API}/cms/refresh", headers=_auth(coder_token), timeout=30)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    def test_cms_refresh_admin(self, admin_token):
        # CMS refresh does HEAD requests to cms.gov with 5s timeout each x5 = up to 25s
        r = requests.post(f"{API}/cms/refresh", headers=_auth(admin_token), timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "refreshed_at" in data
        datasets = data.get("datasets", [])
        assert len(datasets) == 5, f"Expected 5 datasets, got {len(datasets)}: {[d.get('id') for d in datasets]}"
        ids = {d["id"] for d in datasets}
        assert ids == {"lcd", "ncd", "ipps", "ncci", "mue"}, f"Unexpected dataset ids: {ids}"
        for d in datasets:
            assert "name" in d
            assert "source" in d
            assert "reachable" in d
            assert "status_code" in d

    def test_cms_status_after_refresh_populated(self, admin_token, coder_token):
        r = requests.get(f"{API}/cms/status", headers=_auth(coder_token), timeout=15)
        assert r.status_code == 200
        data = r.json()
        # After prior refresh test, this should be populated
        assert data.get("refreshed_at") is not None
        assert len(data.get("datasets", [])) == 5


# ---------- PDF export ----------

def _create_and_process_session(coder_token: str, synthetic_text: str) -> str:
    # Create session
    r = requests.post(
        f"{API}/coding/sessions",
        headers=_auth(coder_token),
        json={"claim_type": "CMS-1500", "codes_required": ["ALL"], "specialty": [], "payer": "MEDICARE"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    sid = r.json()["id"]

    # Upload synthetic text file
    files = {"files": ("record.txt", io.BytesIO(synthetic_text.encode("utf-8")), "text/plain")}
    r = requests.post(f"{API}/coding/sessions/{sid}/upload", headers=_auth(coder_token), files=files, timeout=30)
    assert r.status_code == 200, r.text

    # Process
    r = requests.post(f"{API}/coding/sessions/{sid}/process", headers=_auth(coder_token), timeout=60)
    assert r.status_code == 200, r.text
    return sid


class TestPDFExport:
    def test_pdf_happy_path(self, coder_token):
        text = "Patient John Smith DOB 01/15/1960 pneumonia hypertension cbc cxr"
        sid = _create_and_process_session(coder_token, text)
        r = requests.get(f"{API}/coding/sessions/{sid}/pdf", headers=_auth(coder_token), timeout=30)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500
        assert r.content[:4] == b"%PDF", f"Not a PDF: first bytes={r.content[:8]!r}"

    def test_pdf_unprocessed_returns_400(self, coder_token):
        # Create a session but don't process
        r = requests.post(
            f"{API}/coding/sessions",
            headers=_auth(coder_token),
            json={"claim_type": "CMS-1500", "codes_required": ["ALL"], "specialty": [], "payer": "MEDICARE"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        sid = r.json()["id"]

        r = requests.get(f"{API}/coding/sessions/{sid}/pdf", headers=_auth(coder_token), timeout=15)
        assert r.status_code == 400, r.text
        body = r.json()
        detail = body.get("detail", "")
        assert "not been processed" in detail.lower() or "processed" in detail.lower(), detail

    def test_pdf_requires_auth(self, coder_token):
        # need a valid session id; use one from the happy path — but w/o header
        text = "Patient test pneumonia"
        sid = _create_and_process_session(coder_token, text)
        r = requests.get(f"{API}/coding/sessions/{sid}/pdf", timeout=15)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


# ---------- Expanded coding dictionary ----------

class TestExpandedCatalog:
    def test_expanded_icd10_five_distinct_codes(self, coder_token):
        text = (
            "Chief complaint: diabetes type 2 and hypertension. "
            "History of pneumonia. Reports chest pain and back pain. "
            "Diagnoses include anxiety and obesity."
        )
        sid = _create_and_process_session(coder_token, text)
        r = requests.get(f"{API}/coding/sessions/{sid}", headers=_auth(coder_token), timeout=15)
        assert r.status_code == 200, r.text
        result = r.json().get("coding_result") or {}
        codes: set[str] = set()
        if result.get("principal_diagnosis"):
            codes.add(result["principal_diagnosis"].get("code", ""))
        for c in result.get("secondary_diagnoses") or []:
            codes.add(c.get("code", ""))
        # Keep only ICD-10-CM shape entries (letter + digits, not CPT 5-digit numeric)
        icd_codes = {c for c in codes if c and not c.isdigit()}
        assert len(icd_codes) >= 5, f"Expected >=5 distinct ICD-10-CM codes, got {icd_codes} (all={codes})"

    def test_expanded_cpt_five_codes(self, coder_token):
        text = (
            "Orders: chest x-ray, EKG, CBC, BMP. "
            "Office visit established patient level 3."
        )
        sid = _create_and_process_session(coder_token, text)
        r = requests.get(f"{API}/coding/sessions/{sid}", headers=_auth(coder_token), timeout=15)
        assert r.status_code == 200, r.text
        result = r.json().get("coding_result") or {}
        cpt_codes: set[str] = set()
        if result.get("principal_procedure"):
            cpt_codes.add(result["principal_procedure"].get("code", ""))
        for c in result.get("additional_procedures") or []:
            cpt_codes.add(c.get("code", ""))
        cpt_codes.discard("")
        assert len(cpt_codes) >= 5, f"Expected >=5 CPT codes, got {cpt_codes}"


# ---------- Admin approve email path (endpoint doesn't 500) ----------

class TestAdminApproveEmail:
    def test_approve_nonexistent_user_returns_404_not_500(self, admin_token):
        # Should return 404 cleanly, verifying no unhandled email exception
        fake_id = "00000000-0000-0000-0000-000000000000"
        r = requests.post(
            f"{API}/admin/users/{fake_id}/approve",
            headers=_auth(admin_token),
            json={"reason": ""},
            timeout=15,
        )
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_approve_existing_coder_idempotent_no_500(self, admin_token):
        # Approving already-approved coder should still return 200 (no email exception)
        r = requests.get(f"{API}/admin/users", headers=_auth(admin_token), timeout=15)
        assert r.status_code == 200
        users = r.json()
        coder = next((u for u in users if u["email"] == CODER_EMAIL), None)
        assert coder, "Seeded coder not found"
        r = requests.post(
            f"{API}/admin/users/{coder['id']}/approve",
            headers=_auth(admin_token),
            json={"reason": ""},
            timeout=30,
        )
        assert r.status_code == 200, f"Approve should succeed (email may fail silently): {r.status_code} {r.text}"


# ---------- CORS hardening ----------
# NOTE: Through the public URL the Cloudflare/Kubernetes edge overrides CORS
# headers with a wildcard on OPTIONS preflights. To validate the backend's
# own CORS hardening we hit the backend directly on localhost:8001.

BACKEND_DIRECT = "http://localhost:8001"


class TestCORS:
    def test_cors_preflight_returns_configured_origin_direct(self):
        """Backend CORSMiddleware must echo the allowed origin, not '*'."""
        r = requests.options(
            f"{BACKEND_DIRECT}/api/auth/login",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=10,
        )
        assert r.status_code in (200, 204), f"Preflight status={r.status_code}: {r.text}"
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao == ALLOWED_ORIGIN, f"Expected ACAO={ALLOWED_ORIGIN}, got {acao!r}"
        assert acao != "*", "CORS must not be wildcard when credentials are allowed"
        acac = r.headers.get("access-control-allow-credentials", "")
        assert acac.lower() == "true", f"Expected credentials=true, got {acac!r}"

    def test_cors_disallowed_origin_rejected_direct(self):
        """Backend must reject preflight from unknown origin."""
        r = requests.options(
            f"{BACKEND_DIRECT}/api/auth/login",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=10,
        )
        # Starlette CORSMiddleware returns 400 for disallowed origins on preflight
        assert r.status_code == 400, f"Expected 400 for disallowed origin, got {r.status_code}"
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "https://evil.example.com", f"Disallowed origin was echoed: {acao}"
