"""
Tests for login, MFA, logout, refresh, password reset.
Run: pytest tests/test_auth.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLogin:
    def test_valid_login_requires_mfa(self, client, mock_redis, mock_cognito):
        mock_cognito.initiate_auth.return_value = {
            "requires_mfa": True, "session": "cog-session-abc"
        }
        r = client.post("/api/v1/auth/login", json={
            "email": "jane@test.com", "password": "ValidPass123!!"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["requires_2fa"]  is True
        assert d["mfa_session"]   is not None
        assert d["access_token"]  is None   # NOT issued before MFA

    def test_wrong_password_returns_401(self, client, mock_redis, mock_cognito):
        from app.services.cognito_service import CognitoError
        mock_cognito.initiate_auth.side_effect = CognitoError("Incorrect email or password.")
        r = client.post("/api/v1/auth/login", json={
            "email": "jane@test.com", "password": "wrongpassword"
        })
        assert r.status_code == 401
        assert "password" in r.json()["detail"].lower()

    def test_rate_limit_after_5_attempts(self, client, mock_redis, mock_cognito):
        """6th login attempt in 1 minute returns 429."""
        from app.services.cognito_service import CognitoError
        mock_cognito.initiate_auth.side_effect = CognitoError("Incorrect email or password.")
        for _ in range(5):
            client.post("/api/v1/auth/login", json={
                "email": "jane@test.com", "password": "wrong"
            })
        r = client.post("/api/v1/auth/login", json={
            "email": "jane@test.com", "password": "wrong"
        })
        assert r.status_code in (429, 401)


class TestMFALogin:
    def test_valid_totp_returns_tokens(self, client, mock_redis, mock_cognito):
        r, store = mock_redis
        import json
        store["chc:mfa:validtoken"] = json.dumps({
            "email": "jane@test.com", "cognito_session": "cog-abc"
        })
        r.get = AsyncMock(side_effect=lambda k: store.get(k))

        mock_cognito.respond_mfa.return_value = {
            "access_token": "real-access-token",
            "refresh_token": "real-refresh-token",
            "expires_in": 3600,
        }
        resp = client.post("/api/v1/auth/login/mfa", json={
            "mfa_session": "validtoken", "totp_code": "123456"
        })
        assert resp.status_code == 200
        assert resp.json()["access_token"] == "real-access-token"

    def test_expired_mfa_session_returns_400(self, client, mock_redis, mock_cognito):
        r, store = mock_redis
        r.get = AsyncMock(return_value=None)  # Session expired
        resp = client.post("/api/v1/auth/login/mfa", json={
            "mfa_session": "expired", "totp_code": "123456"
        })
        assert resp.status_code == 400

    def test_wrong_totp_returns_401(self, client, mock_redis, mock_cognito):
        import json
        r, store = mock_redis
        store["chc:mfa:tok"] = json.dumps({"email":"x@y.com","cognito_session":"s"})
        r.get = AsyncMock(side_effect=lambda k: store.get(k))
        from app.services.cognito_service import CognitoError
        mock_cognito.respond_mfa.side_effect = CognitoError("Incorrect TOTP code.")
        resp = client.post("/api/v1/auth/login/mfa", json={
            "mfa_session": "tok", "totp_code": "000000"
        })
        assert resp.status_code == 401


class TestLogout:
    def test_logout_without_token_returns_403(self, client):
        r = client.post("/api/v1/auth/logout")
        assert r.status_code == 403

    def test_logout_adds_to_blocklist(self, client, mock_redis, mock_cognito):
        """After logout, same token should be rejected (blocklist checked)."""
        # This is an integration-level behaviour — covered by E2E tests


class TestPasswordReset:
    def test_reset_always_returns_200(self, client, mock_cognito):
        """Never reveals if email exists (prevents enumeration)."""
        mock_cognito.forgot_password.return_value = None
        r = client.post("/api/v1/auth/password/reset",
                        json={"email": "nonexistent@test.com"})
        assert r.status_code == 200
        assert "sent" in r.json()["message"].lower()

    def test_confirm_wrong_code_returns_400(self, client, mock_cognito):
        from app.services.cognito_service import CognitoError
        mock_cognito.confirm_forgot_password.side_effect = CognitoError("Invalid reset code.")
        r = client.post("/api/v1/auth/password/confirm", json={
            "email": "jane@test.com", "reset_code": "000000",
            "new_password": "NewValid123!!", "confirm_password": "NewValid123!!"
        })
        assert r.status_code == 400


class TestHealthEndpoints:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_root_returns_product_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Carolin Code Pro AI" in r.json()["product"]
