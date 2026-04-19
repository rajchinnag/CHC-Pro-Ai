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

## 5. What's been implemented (2026-02-19)

### Backend (`/app/backend`)
- `auth_utils.py` — bcrypt, JWT (access + refresh + MFA-challenge + registration stage tokens), TOTP, QR PNG as base64, validators (NPI / EIN / password strength).
- `phi_purger.py` — 18-category Safe-Harbor redaction via regex + contextual
  rules for names / DOB / age>89 / provider names.
- `coding_engine.py` — dictionaries for ICD-10-CM, ICD-10-PCS, CPT, HCPCS,
  Revenue, Condition, Occurrence, Value codes + MS-DRG grouper + MUE/NCCI
  edit checks + payer-aware processing log.
- `ocr_service.py` — Tesseract + pdfplumber + python-docx extraction.
- `server.py` — FastAPI app with all routes under `/api`:
  - Auth: `/register`, `/verify-otp`, `/confirm-mfa`, `/login`, `/login-mfa`,
    `/refresh`, `/me`, `/logout`
  - Admin: `/admin/pending`, `/admin/users`, `/admin/users/{id}/approve|reject|suspend`, `/admin/audit`
  - Coding: `/coding/sessions` (create / list), `/coding/sessions/{id}` (get /
    delete), `/coding/sessions/{id}/upload`, `/coding/sessions/{id}/process`
  - Settings: `/settings/change-password`, `/settings/reset-mfa`,
    `/settings/confirm-mfa-reset`
  - `GET /api/captcha` — local arithmetic challenge (no 3rd-party).
- Startup: indexes, admin + coder seeding, hourly 24h-purge background task.
- **27/27 backend tests passing** (see `/app/backend/tests/backend_test.py`).

### Frontend (`/app/frontend`)
- Routes: `/`, `/login`, `/register`, `/app/{dashboard,wizard,results/:id,history,settings,help,admin/pending,admin/users,admin/audit}`.
- Landing (split panel), Login (2-step w/ MFA), Register (4-stage w/ OTP + QR).
- Dashboard, 6-step coding wizard, Results page with CSV export,
  History (24h), Admin Pending/Users/Audit, Settings (change password,
  reset MFA).
- AuthContext with bearer-token storage, 5-min idle logout + 60s warning modal.
- Tailwind config + IBM Plex Sans/Mono fonts + healthcare blue palette.
- `data-testid` on every interactive element.

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
