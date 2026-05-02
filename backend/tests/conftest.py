"""
Shared pytest fixtures for Layer 1 tests.
All AWS calls are mocked — no real AWS account needed to run tests.
"""
import json, pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Patch settings before importing app
os.environ.update({
    "AWS_ACCESS_KEY_ID":       "test",
    "AWS_SECRET_ACCESS_KEY":   "test",
    "COGNITO_USER_POOL_ID":    "us-east-1_TEST",
    "COGNITO_CLIENT_ID":       "testclientid",
    "COGNITO_CLIENT_SECRET":   "testclientsecret",
    "JWT_SECRET_KEY":          "testsecretkey",
    "DATABASE_URL":            "postgresql://test:test@localhost/test",
    "REDIS_URL":               "redis://localhost:6379/0",
})

from main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_redis(monkeypatch):
    store = {}
    r = MagicMock()
    r.get    = AsyncMock(side_effect=lambda k: store.get(k))
    r.setex  = AsyncMock(side_effect=lambda k,t,v: store.update({k:v}))
    r.delete = AsyncMock(side_effect=lambda k: store.pop(k, None))
    r.ping   = AsyncMock(return_value=True)
    r.incr   = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    r.ttl    = AsyncMock(return_value=1800)
    r.pipeline = MagicMock(return_value=MagicMock(
        setex=MagicMock(), incr=MagicMock(), expire=MagicMock(),
        execute=AsyncMock(return_value=[True,1,True])
    ))
    monkeypatch.setattr("app.services.otp_service._redis", r)
    return r, store

@pytest.fixture
def mock_cognito(monkeypatch):
    mock = MagicMock()
    mock.user_exists.return_value          = False
    mock.create_user.return_value          = "test-user-uuid-1234"
    mock.set_permanent_password.return_value = None
    mock.enable_mfa.return_value           = None
    mock.get_user.return_value             = {
        "sub": "test-user-uuid-1234", "email": "test@example.com",
        "given_name": "Test", "family_name": "User",
        "custom:npi": "1234567890", "custom:specialty": "internal_medicine",
        "custom:state": "TX", "email_verified": "true",
        "custom:mfa_enabled": "true", "custom:pecos": "True",
    }
    mock.initiate_auth.return_value        = {
        "requires_mfa": True, "session": "cognito-session-token"
    }
    mock.respond_mfa.return_value          = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
    }
    monkeypatch.setattr("app.routes.registration.cognito", mock)
    monkeypatch.setattr("app.routes.auth.cognito",         mock)
    return mock
