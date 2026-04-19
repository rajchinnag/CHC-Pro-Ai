"""Google reCAPTCHA v2 verification with local arithmetic fallback.

When `RECAPTCHA_SECRET_KEY` is configured we verify via Google's
siteverify endpoint. Otherwise we fall back to a local arithmetic captcha
where the server issues a math question and verifies the answer itself.
"""
from __future__ import annotations
import os
import secrets
import logging
from typing import Tuple

import requests

logger = logging.getLogger("chcpro.captcha")

# In-memory store for local arithmetic fallback
_LOCAL: dict[str, int] = {}
_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def recaptcha_enabled() -> bool:
    k = os.environ.get("RECAPTCHA_SECRET_KEY", "").strip()
    return bool(k) and not k.startswith("6LfGyb4sAAAAAFmfxlCi5BNmfkhojxrJz5ExsrCx_placeholder")


def issue_local_challenge() -> dict:
    """Issue an arithmetic challenge for the fallback captcha."""
    a = secrets.randbelow(9) + 1
    b = secrets.randbelow(9) + 1
    op = secrets.choice(["+", "-", "×"])
    if op == "+":
        answer = a + b
    elif op == "-":
        if b > a:
            a, b = b, a
        answer = a - b
    else:
        answer = a * b
    token = secrets.token_urlsafe(16)
    _LOCAL[token] = answer
    if len(_LOCAL) > 1000:
        _LOCAL.clear()
    return {"token": token, "question": f"{a} {op} {b} = ?", "mode": "local"}


def issue_challenge() -> dict:
    """Return captcha config for the client."""
    if recaptcha_enabled():
        return {"mode": "recaptcha_v2", "site_key_hint": "use REACT_APP_RECAPTCHA_SITE_KEY"}
    return issue_local_challenge()


def verify(token: str, answer: str | None = None, remote_ip: str | None = None) -> Tuple[bool, str]:
    """Verify a captcha response.

    For reCAPTCHA v2, `token` is the g-recaptcha-response from the client.
    For local fallback, `token` is the challenge token and `answer` is the user's answer.
    """
    if recaptcha_enabled():
        if not token:
            return False, "Missing reCAPTCHA token"
        try:
            data = {"secret": os.environ["RECAPTCHA_SECRET_KEY"], "response": token}
            if remote_ip:
                data["remoteip"] = remote_ip
            r = requests.post(_VERIFY_URL, data=data, timeout=5)
            res = r.json()
            if res.get("success"):
                return True, "ok"
            errs = ",".join(res.get("error-codes") or []) or "invalid"
            return False, f"reCAPTCHA failed: {errs}"
        except Exception as e:
            logger.error("reCAPTCHA verify error: %s", e)
            # Fail-open ONLY if remote service is unreachable in dev; in prod you'd fail-closed.
            return False, f"reCAPTCHA unreachable: {e}"

    # Local arithmetic fallback
    expected = _LOCAL.pop(token or "", None)
    if expected is None:
        return False, "CAPTCHA token expired or invalid"
    try:
        return int(str(answer or "").strip()) == expected, "ok"
    except Exception:
        return False, "Invalid CAPTCHA answer"
