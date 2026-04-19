"""Resend email wrapper with dev-mode fallback.

When `RESEND_API_KEY` is missing or delivery fails, emails are logged to the
server log so the registration / approval flow still works in development.
"""
from __future__ import annotations
import os
import asyncio
import logging
from typing import Optional

import resend

logger = logging.getLogger("chcpro.email")


def _configured() -> bool:
    key = os.environ.get("RESEND_API_KEY", "").strip()
    return bool(key) and not key.startswith("re_your")


def _sender() -> str:
    name = os.environ.get("SENDER_NAME", "CHC Pro AI")
    addr = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    return f"{name} <{addr}>"


async def send_email(to: str, subject: str, html: str) -> dict:
    """Send an email. Returns {"delivered": bool, "id"|"reason": str}.

    Always logs the subject/body in dev mode so tests can assert behavior
    without hitting Resend.
    """
    logger.info("EMAIL → %s | %s", to, subject)
    if not _configured():
        logger.warning("RESEND_API_KEY not configured — email not actually sent.")
        return {"delivered": False, "reason": "dev-mode: RESEND_API_KEY missing"}

    resend.api_key = os.environ["RESEND_API_KEY"]
    params = {
        "from": _sender(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        res = await asyncio.to_thread(resend.Emails.send, params)
        return {"delivered": True, "id": res.get("id", "")}
    except Exception as e:
        logger.error("Resend send failed: %s", e)
        return {"delivered": False, "reason": str(e)}


# ----- Templates -----

def tpl_otp(otp: str, recipient_name: str = "") -> tuple[str, str]:
    subject = "Your CHC Pro AI verification code"
    html = f"""
    <div style="font-family:'IBM Plex Sans',Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#0F172A;">
      <div style="border-top:4px solid #003F87;padding-top:24px;">
        <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#64748B;margin:0;">CHC Pro AI · Secure verification</p>
        <h1 style="font-size:24px;margin:8px 0 0;">Your one-time code</h1>
        <p style="color:#64748B;margin:12px 0 24px;">Hi {recipient_name or 'there'}, use the code below to verify your email address. This code expires in 10 minutes.</p>
        <div style="background:#F4F8FC;border:1px solid #E2E8F0;border-radius:8px;padding:20px;text-align:center;">
          <p style="font-family:'IBM Plex Mono',monospace;font-size:36px;font-weight:600;letter-spacing:8px;color:#003F87;margin:0;">{otp}</p>
        </div>
        <p style="color:#64748B;font-size:12px;margin-top:24px;">If you did not request this code, please ignore this email or contact your facility administrator.</p>
        <p style="color:#94A3B8;font-size:11px;margin-top:24px;border-top:1px solid #E2E8F0;padding-top:16px;">Sent from a HIPAA-aware platform. No PHI is included in this email.</p>
      </div>
    </div>
    """
    return subject, html


def tpl_approved(recipient_name: str = "") -> tuple[str, str]:
    subject = "Your CHC Pro AI account has been approved"
    html = f"""
    <div style="font-family:'IBM Plex Sans',Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#0F172A;">
      <div style="border-top:4px solid #059669;padding-top:24px;">
        <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#059669;margin:0;">Account approved</p>
        <h1 style="font-size:22px;margin:8px 0 0;">Welcome aboard, {recipient_name or 'Coder'}.</h1>
        <p style="color:#64748B;margin:12px 0 24px;">Your Facility Provider/Administrator has approved your access to CHC Pro AI. You can now sign in and start coding medical records.</p>
        <p style="color:#94A3B8;font-size:11px;margin-top:24px;border-top:1px solid #E2E8F0;padding-top:16px;">CHC Pro AI · HIPAA-aware medical coding platform</p>
      </div>
    </div>
    """
    return subject, html


def tpl_rejected(reason: str, recipient_name: str = "") -> tuple[str, str]:
    subject = "Your CHC Pro AI registration was not approved"
    html = f"""
    <div style="font-family:'IBM Plex Sans',Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#0F172A;">
      <div style="border-top:4px solid #DC2626;padding-top:24px;">
        <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#DC2626;margin:0;">Registration declined</p>
        <h1 style="font-size:22px;margin:8px 0 0;">Hello {recipient_name or 'there'},</h1>
        <p style="color:#64748B;margin:12px 0 12px;">Your registration for CHC Pro AI was not approved by your Facility Provider/Administrator.</p>
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:16px;">
          <p style="margin:0;color:#7F1D1D;"><b>Reason:</b> {reason or 'Not specified'}</p>
        </div>
        <p style="color:#64748B;font-size:12px;margin-top:24px;">Please contact your administrator for next steps.</p>
      </div>
    </div>
    """
    return subject, html


def tpl_new_registration_admin(user_email: str, user_name: str, user_npi: str) -> tuple[str, str]:
    subject = "New CHC Pro AI registration awaiting approval"
    html = f"""
    <div style="font-family:'IBM Plex Sans',Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#0F172A;">
      <div style="border-top:4px solid #003F87;padding-top:24px;">
        <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#64748B;margin:0;">Approval required</p>
        <h1 style="font-size:22px;margin:8px 0 0;">A new user needs your review</h1>
        <div style="background:#F4F8FC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;margin:16px 0;">
          <p style="margin:0 0 4px;font-size:12px;color:#64748B;">Name</p>
          <p style="margin:0 0 12px;font-family:'IBM Plex Mono',monospace;">{user_name}</p>
          <p style="margin:0 0 4px;font-size:12px;color:#64748B;">Email</p>
          <p style="margin:0 0 12px;font-family:'IBM Plex Mono',monospace;">{user_email}</p>
          <p style="margin:0 0 4px;font-size:12px;color:#64748B;">NPI</p>
          <p style="margin:0;font-family:'IBM Plex Mono',monospace;">{user_npi}</p>
        </div>
        <p style="color:#64748B;font-size:13px;">Sign in to CHC Pro AI and open <b>Admin → Pending Approvals</b> to review.</p>
      </div>
    </div>
    """
    return subject, html
