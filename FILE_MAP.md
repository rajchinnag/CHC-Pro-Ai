# Layer 1 — File Map
## Where every file goes in your CHC-Pro-Ai repo

### Files to DELETE from repo first
```
git rm -r .emergent/         # Emergent agent state — not app code
git rm -r memory/            # Emergent agent memory — not app code
git rm --cached .gitconfig   # Personal git config — never commit
```
Then add to .gitignore: .emergent/ memory/ .gitconfig

---

### Backend files → backend/

| This file                                    | Goes to                                        |
|----------------------------------------------|------------------------------------------------|
| backend/main.py                              | backend/main.py  (REPLACE existing)            |
| backend/config.py                            | backend/config.py  (NEW)                       |
| backend/requirements.txt                     | backend/requirements.txt  (REPLACE existing)   |
| backend/.env.example                         | .env.example  (root level)                     |
| backend/alembic.ini                          | backend/alembic.ini  (NEW)                     |
| backend/pytest.ini                           | backend/pytest.ini  (NEW)                      |
| backend/app/__init__.py                      | backend/app/__init__.py  (NEW)                 |
| backend/app/schemas/__init__.py              | backend/app/schemas/__init__.py  (NEW)         |
| backend/app/schemas/auth_schemas.py          | backend/app/schemas/auth_schemas.py  (NEW)     |
| backend/app/db/__init__.py                   | backend/app/db/__init__.py  (NEW)              |
| backend/app/db/models.py                     | backend/app/db/models.py  (NEW)                |
| backend/app/db/session.py                    | backend/app/db/session.py  (NEW)               |
| backend/app/db/migrations/__init__.py        | backend/app/db/migrations/__init__.py  (NEW)   |
| backend/app/db/migrations/env.py             | backend/app/db/migrations/env.py  (NEW)        |
| backend/app/db/migrations/versions/0001...py | backend/app/db/migrations/versions/  (NEW)     |
| backend/app/services/__init__.py             | backend/app/services/__init__.py  (NEW)        |
| backend/app/services/cognito_service.py      | backend/app/services/cognito_service.py  (NEW) |
| backend/app/services/npi_service.py          | backend/app/services/npi_service.py  (NEW)     |
| backend/app/services/otp_service.py          | backend/app/services/otp_service.py  (NEW)     |
| backend/app/services/esignature_service.py   | backend/app/services/esignature_service.py (NEW)|
| backend/app/services/audit_service.py        | backend/app/services/audit_service.py  (NEW)   |
| backend/app/middleware/__init__.py            | backend/app/middleware/__init__.py  (NEW)      |
| backend/app/middleware/auth_middleware.py     | backend/app/middleware/auth_middleware.py (NEW)|
| backend/app/routes/__init__.py               | backend/app/routes/__init__.py  (NEW)          |
| backend/app/routes/auth.py                   | backend/app/routes/auth.py  (NEW)              |
| backend/app/routes/registration.py           | backend/app/routes/registration.py  (NEW)      |
| backend/tests/__init__.py                    | backend/tests/__init__.py  (NEW)               |
| backend/tests/conftest.py                    | backend/tests/conftest.py  (NEW)               |
| backend/tests/test_auth.py                   | backend/tests/test_auth.py  (NEW)              |
| backend/tests/test_registration.py           | backend/tests/test_registration.py  (NEW)      |

---

### Frontend files → frontend/src/

| This file                                         | Goes to                                             |
|---------------------------------------------------|-----------------------------------------------------|
| frontend/src/services/authService.js              | frontend/src/services/authService.js  (NEW)         |
| frontend/src/hooks/useAuth.js                     | frontend/src/hooks/useAuth.js  (NEW)                |
| frontend/src/components/ProtectedRoute.jsx        | frontend/src/components/ProtectedRoute.jsx  (NEW)   |
| frontend/src/components/OTPInput.jsx              | frontend/src/components/OTPInput.jsx  (NEW)         |
| frontend/src/components/SignatureCanvas.jsx       | frontend/src/components/SignatureCanvas.jsx  (NEW)  |
| frontend/src/components/WizardStepper.jsx         | frontend/src/components/WizardStepper.jsx  (NEW)    |
| frontend/src/pages/Login.jsx                      | frontend/src/pages/Login.jsx  (REPLACE existing)    |
| frontend/src/pages/Register.jsx                   | frontend/src/pages/Register.jsx  (REPLACE existing) |

---

### Root level

| This file       | Goes to              |
|-----------------|----------------------|
| .gitignore      | .gitignore  (REPLACE)|
| README.md       | README.md  (REPLACE) |
| FILE_MAP.md     | FILE_MAP.md  (NEW)   |
