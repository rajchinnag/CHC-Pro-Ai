# CHC Pro AI — Product Requirements Document

_Last updated: 2026-02-19_

## 1. Problem statement

Build a HIPAA-aware, standalone AI-powered Medical Coding and Billing web
application called **CHC Pro AI**. A secure, multi-step, role-based web app
for healthcare billing professionals. It performs OCR on uploaded medical
records, purges PHI internally without any external AI services, then applies
payer-specific coding guidelines to generate ICD-10, CPT, HCPCS, Revenue,
Condition, Occurrence, Value, MS-DRG codes for UB-04 and CMS-1500 claim forms.

Color palette: Healthcare Blue (`#003F87`, `#0073CF`) on Clean White
(`#FFFFFF`, `#F4F8FC`) with accent teal (`#00AEEF`). Typography: IBM Plex
Sans / IBM Plex Mono.

## 2. User personas

- **Medical Coder** — registers with NPI / Tax ID / Email / Full name / DOB /
  Security Q+A / Password / CAPTCHA / Email OTP / MFA. After admin approval,
  logs in via password + TOTP. Uploads one patient encounter per session and
  receives payer-specific coded output.
- **Facility Provider / Admin** — receives notifications for new registrations,
  approves / rejects / suspends users, reviews audit logs.

## 3. Tech architecture

- **Frontend:** React 19 + Tailwind + shadcn/ui + @phosphor-icons/react +
  react-router-dom + sonner.
- **Backend:** FastAPI (Python 3.11) + motor (Mongo).
- **OCR:** Tesseract 5 (system package), `pytesseract`, `pdfplumber`,
  `python-docx`.
- **PHI purging:** Rule-based regex + NLP pipeline (`phi_purger.py`) —
  entirely in-process, no external AI calls.
- **Coding engine:** Internal rule-based dictionary (`coding_engine.py`) with
  ICD-10-CM, ICD-10-PCS, CPT, HCPCS, MS-DRG, Revenue, Condition, Occurrence,
  Value codes + MUE / NCCI edit checks.
- **Auth:** Custom JWT (access 15 min, refresh 7d) + TOTP (`pyotp`, RFC 6238)
  + QR code (`qrcode`). Local arithmetic CAPTCHA. Dev-mode OTP returned in
  response body.
- **Database:** MongoDB.

## 4. Core requirements (static)

1. Registration with multi-step verification (Email OTP → MFA QR).
2. Admin approval gate — blocks login for unapproved users.
3. TOTP MFA mandatory after registration.
4. 5-minute idle logout with 60s warning.
5. 24-hour auto-purge on all uploaded records + coding results.
6. Max 2 coding sessions retained per user (business rule).
7. Real OCR on PDF / image / DOCX input.
8. Rule-based PHI Safe-Harbor redaction covering 18 categories.
9. Payer-aware coding (Medicare / Medicaid+state / Commercial).
10. MUE + NCCI edit validation on every result.
11. Full audit trail (no PHI in logs).
12. No external AI APIs at any stage.

## 5. What's been implemented

### Phase 1 (2026-02-19) — MVP
- `auth_utils.py` — bcrypt, JWT (access + refresh + MFA-challenge + registration stage tokens), TOTP, QR PNG as base64, validators (NPI / EIN / password strength).
- `phi_purger.py` — 18-category Safe-Harbor redaction.
- `coding_engine.py` — ICD/CPT/HCPCS/MS-DRG dictionaries with MUE+NCCI edits (~60 codes).
- `ocr_service.py` — Tesseract + pdfplumber + python-docx.
- `server.py` — FastAPI app with all /api routes (auth, admin, coding, settings), startup indexes, admin + coder seeding, 24h purge loop.
- Frontend: Landing, Login (2-step MFA), Register (4-stage OTP+QR), Dashboard, 6-step Wizard, Results (CSV export), History, Admin Pending/Users/Audit, Settings.
- Idle-logout + 60s warning modal, bearer-token auth, healthcare-blue design in IBM Plex Sans/Mono.
- **27/27 Phase 1 backend tests passing.**

### Phase 2 (2026-02-19 evening) — Integrations & depth
- **Resend email** (`email_service.py`) — OTP, approval, rejection, and admin-notification templates. Dev-mode fallback when key missing.
- **Google reCAPTCHA v2** (`captcha_service.py`) — real Google siteverify + local arithmetic fallback. Frontend uses `react-google-recaptcha` with `REACT_APP_RECAPTCHA_SITE_KEY`.
- **Expanded dictionary** (`code_catalog.py`) — ~550 entries across ICD-10-CM, ICD-10-PCS, CPT, HCPCS, Revenue, Condition, Occurrence, Value codes + MS-DRG mappings.
- **PDF export** (`pdf_export.py`) — reportlab server-rendered PDF with healthcare-blue styling; `GET /api/coding/sessions/{id}/pdf` endpoint.
- **CMS LCD/NCD refresh** (`cms_refresh.py`) — monthly background task; `GET /api/cms/status` + admin-only `POST /api/cms/refresh`; dashboard "Last refreshed" badge + manual Refresh button.
- **CORS hardening** — explicit origins from `CORS_ORIGINS` env.
- **17/17 Phase 2 backend tests passing.**

### Seeded accounts
- Admin — `admin@chcpro.ai` / `AdminPass@2025!` (no MFA)
- Coder — `coder@chcpro.ai` / `CoderPass@2025!` (no MFA, approved)

## 6. Backlog

### P1
- Real email delivery (Resend / SendGrid) for OTP + approval notifications.
- Real CAPTCHA provider (hCaptcha / reCAPTCHA v2).
- PDF export of coding results (currently CSV only).
- Role-scoped coding session creation (admins currently also have coding
  access since only `approved` is checked).

### P2
- Persistent encrypted file storage with server-side key management
  (current MVP stores raw bytes in Mongo, purged immediately post-process).
- Provider portal: per-facility user list and activity dashboards.
- ICD-10-CM / CPT dictionary expansion (current MVP covers ~60 codes).
- ICD-10 annual update ingestion pipeline.
- Multi-tenant facility separation at DB level.

### P3
- Role "Provider" with subset of admin abilities (approve only own facility).
- Specialty-specific coding rules (e.g., OB/GYN global periods).
- APR-DRG grouper (currently MS-DRG only).

## 7. Next tasks
- Expand ICD-10 / CPT dictionary coverage.
- Integrate real SMTP provider for registration + approval notifications.
- Add per-session PDF export.
- Finalize prod CORS policy and ingest LCD updates monthly.
