# 🗄️ Backend — Prompt Polisher API

> **Tech Stack**: FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 · Redis 7 · Celery · Pydantic v2

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API Docs → http://localhost:8000/docs
```

## Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Pydantic Settings
│   ├── dependencies.py      # Dependency injection
│   ├── middleware/           # Auth, rate limiting, CORS
│   ├── api/v1/              # API route handlers
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   ├── core/                # Security, database config
│   └── tasks/               # Celery async tasks
├── alembic/                 # Database migrations
├── tests/                   # Pytest test suite
├── requirements.txt
└── Dockerfile
```

## Owner
🗄️ **Data / Backend Engineer** (Member D)
