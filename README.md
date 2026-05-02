# Carolin Code Pro AI — Layer 1: Auth & Registration

HIPAA-compliant provider authentication and 5-step registration.

## Setup

```bash
cd backend
cp .env.example .env        # Fill in your AWS values
pip install -r requirements.txt
alembic upgrade head        # Run DB migrations
uvicorn main:app --reload   # Start API on :8000
```

```bash
cd frontend
npm install
npm start                   # Start React on :3000
```

## API docs
http://localhost:8000/docs

## Tests
```bash
cd backend && pytest -v
```

## File locations
See FILE_MAP.md for where every file goes in your repo.
