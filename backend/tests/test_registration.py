"""
Tests for all 5 registration steps.
Run: pytest tests/test_registration.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────

VALID_STEP1 = {
    "first_name":    "Jane",
    "last_name":     "Smith",
    "email":         "jane@test.com",
    "phone":         "5551234567",
    "provider_type": "individual",
    "specialty":     "internal_medicine",
    "state":         "TX",
}

VALID_NPI   = "1234567890"
VALID_TAXID = "123456789"


# ── Step 1 ─────────────────────────────────────────────────────────────────

class TestStep1:
    def test_valid_input_returns_session_token(self, client, mock_redis, mock_cognito):
        r = client.post("/api/v1/auth/register/step1", json=VALID_STEP1)
        assert r.status_code == 200
        assert "session_token" in r.json()
        assert len(r.json()["session_token"]) > 20

    def test_duplicate_email_returns_409(self, client, mock_redis, mock_cognito):
        mock_cognito.user_exists.return_value = True
        r = client.post("/api/v1/auth/register/step1", json=VALID_STEP1)
        assert r.status_code == 409
        assert "already exists" in r.json()["detail"].lower()

    def test_invalid_state_returns_422(self, client, mock_redis, mock_cognito):
        data = {**VALID_STEP1, "state": "ZZ"}
        r = client.post("/api/v1/auth/register/step1", json=data)
        assert r.status_code == 422

    def test_invalid_phone_returns_422(self, client, mock_redis, mock_cognito):
        data = {**VALID_STEP1, "phone": "123"}
        r = client.post("/api/v1/auth/register/step1", json=data)
        assert r.status_code == 422

    def test_missing_specialty_returns_422(self, client, mock_redis, mock_cognito):
        data = {**VALID_STEP1}
        del data["specialty"]
        r = client.post("/api/v1/auth/register/step1", json=data)
        assert r.status_code == 422


# ── Step 2 ─────────────────────────────────────────────────────────────────

class TestStep2:
    def _session_token(self, client, mock_redis, mock_cognito):
        r = client.post("/api/v1/auth/register/step1", json=VALID_STEP1)
        return r.json()["session_token"]

    @patch("app.routes.registration.verify_npi")
    @patch("app.routes.registration.check_oig")
    @patch("app.routes.registration.check_pecos")
    def test_valid_npi_returns_detail(self, mock_pecos, mock_oig, mock_npi,
                                      client, mock_redis, mock_cognito):
        from app.schemas.auth_schemas import NPIDetail
        mock_npi.return_value = NPIDetail(
            npi=VALID_NPI, provider_name="Dr. Jane Smith",
            entity_type="Individual", status="A",
            taxonomy_codes=["207R00000X — Internal Medicine"],
            practice_address={"city":"Austin","state":"TX"},
        )
        mock_oig.return_value   = True
        mock_pecos.return_value = True

        token = self._session_token(client, mock_redis, mock_cognito)
        r = client.post("/api/v1/auth/register/step2/verify-npi", json={
            "session_token": token, "npi": VALID_NPI,
            "tax_id": VALID_TAXID, "entity_type": "1",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["npi_verified"]   is True
        assert d["oig_clear"]      is True
        assert d["pecos_enrolled"] is True

    @patch("app.routes.registration.verify_npi")
    def test_invalid_npi_returns_422(self, mock_npi, client, mock_redis, mock_cognito):
        from app.services.npi_service import NPIError
        mock_npi.side_effect = NPIError("NPI not found")
        token = self._session_token(client, mock_redis, mock_cognito)
        r = client.post("/api/v1/auth/register/step2/verify-npi", json={
            "session_token": token, "npi": VALID_NPI,
            "tax_id": VALID_TAXID, "entity_type": "1",
        })
        assert r.status_code == 422

    @patch("app.routes.registration.verify_npi")
    @patch("app.routes.registration.check_oig")
    def test_oig_excluded_returns_403(self, mock_oig, mock_npi,
                                       client, mock_redis, mock_cognito):
        from app.schemas.auth_schemas import NPIDetail
        from app.services.npi_service import OIGExcludedError
        mock_npi.return_value = NPIDetail(
            npi=VALID_NPI, provider_name="Bad Actor",
            entity_type="Individual", status="A",
            taxonomy_codes=[], practice_address={},
        )
        mock_oig.side_effect = OIGExcludedError("Excluded")
        token = self._session_token(client, mock_redis, mock_cognito)
        r = client.post("/api/v1/auth/register/step2/verify-npi", json={
            "session_token": token, "npi": VALID_NPI,
            "tax_id": VALID_TAXID, "entity_type": "1",
        })
        assert r.status_code == 403

    def test_9digit_npi_rejected_before_api(self, client, mock_redis, mock_cognito):
        """NPI validation happens in Pydantic before any external API call."""
        token = self._session_token(client, mock_redis, mock_cognito)
        r = client.post("/api/v1/auth/register/step2/verify-npi", json={
            "session_token": token, "npi": "123456789",  # 9 digits
            "tax_id": VALID_TAXID, "entity_type": "1",
        })
        assert r.status_code == 422


# ── Step 3 OTP ─────────────────────────────────────────────────────────────

class TestStep3:
    @patch("app.routes.registration.send_otp_email", new_callable=AsyncMock)
    @patch("app.routes.registration.generate_otp",   new_callable=AsyncMock)
    def test_send_otp_returns_200(self, mock_gen, mock_send, client, mock_redis, mock_cognito):
        mock_gen.return_value = "123456"
        # Need a valid session with email
        import asyncio
        from app.services.otp_service import session_create
        token = asyncio.get_event_loop().run_until_complete(
            session_create("jane@test.com", {"first_name":"Jane","phone":"5551234567",
                                              "email":"jane@test.com"})
        )
        r = client.post("/api/v1/auth/register/step3/send-otp", json={
            "session_token": token, "channel": "email"
        })
        assert r.status_code == 200
        assert "expires_in" in r.json()


# ── Password validation ────────────────────────────────────────────────────

class TestPasswordValidation:
    def test_short_password_422(self, client):
        from app.schemas.auth_schemas import SetPasswordRequest
        import pytest
        with pytest.raises(Exception):
            SetPasswordRequest(session_token="x", password="Short1!", confirm_password="Short1!")

    def test_no_uppercase_422(self, client):
        from app.schemas.auth_schemas import SetPasswordRequest
        import pytest
        with pytest.raises(Exception):
            SetPasswordRequest(session_token="x", password="alllower123!!", confirm_password="alllower123!!")

    def test_mismatch_422(self, client):
        from app.schemas.auth_schemas import SetPasswordRequest
        import pytest
        with pytest.raises(Exception):
            SetPasswordRequest(session_token="x", password="ValidPass1!!", confirm_password="Different1!!")

    def test_valid_password_ok(self):
        from app.schemas.auth_schemas import SetPasswordRequest
        m = SetPasswordRequest(
            session_token="x", password="ValidPass123!!", confirm_password="ValidPass123!!"
        )
        assert m.password == "ValidPass123!!"
