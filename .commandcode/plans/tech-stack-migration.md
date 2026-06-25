# Tech Stack Migration Plan

**Goal**: Switch from Flask + SQLite + pip to FastAPI + PostgreSQL + uv, and add ruff-based code verification.

---

## Summary of Changes

| Area | Current | New |
|------|---------|-----|
| Web framework | Flask 3.0 | FastAPI |
| ORM | Flask-SQLAlchemy (sync) | SQLAlchemy 2.0 async |
| Database | SQLite | PostgreSQL |
| Driver | sqlite3 | asyncpg |
| Dependency mgmt | pip + requirements.txt | uv + pyproject.toml |
| Linter/formatter | None | ruff |
| ASGI/WSGI server | gunicorn | uvicorn |
| App structure | Single app.py | src/ package (routes, schemas, services) |

---

## File Changes

### New files to create

| # | Path | Purpose |
|---|------|---------|
| 1 | `pyproject.toml` | uv project config, dependencies, ruff settings |
| 2 | `.pre-commit-config.yaml` | ruff hooks on commit |
| 3 | `.github/workflows/ci.yml` | ruff check on push/PR |
| 4 | `src/__init__.py` | Package marker |
| 5 | `src/config.py` | pydantic-settings for environment variables |
| 6 | `src/database.py` | Async engine, sessionmaker, `get_db` dependency |
| 7 | `src/models.py` | SQLAlchemy 2.0 async models (same schema, mapped_column) |
| 8 | `src/seed.py` | Async seed function + CLI entry (`python -m src.seed`) |
| 9 | `src/schemas/__init__.py` | Package marker |
| 10 | `src/schemas/client.py` | Pydantic v2 schemas for client CRUD |
| 11 | `src/schemas/report.py` | Pydantic schemas for report generation |
| 12 | `src/services/__init__.py` | Package marker |
| 13 | `src/services/client_service.py` | Client CRUD logic (extracted from app.py) |
| 14 | `src/services/report_service.py` | Report generation + calculation logic |
| 15 | `src/routes/__init__.py` | Package marker |
| 16 | `src/routes/pages.py` | Jinja2 page routes (dashboard, client form, report form, history) |
| 17 | `src/routes/api.py` | REST API routes (clients CRUD, reports, PDF download) |
| 18 | `src/main.py` | FastAPI app, lifespan, static mount, router registration |
| 19 | `tests/__init__.py` | Package marker |
| 20 | `tests/conftest.py` | Async fixtures with in-memory SQLite for tests |
| 21 | `tests/test_api.py` | Adapted test suite using httpx.AsyncClient |

### Files to modify

| # | Path | Changes |
|---|------|---------|
| 1 | `.env` | Replace `RAILWAY_DATABASE_PATH` with `DATABASE_URL=postgresql+asyncpg://...` |
| 2 | `.env.example` | Same as .env, add comment for Railway's native DATABASE_URL |
| 3 | `Procfile` | `web: uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| 4 | `.gitignore` | Add `.ruff_cache/` (already present), `src/__pycache__/` |

### Files to delete

| # | Path | Reason |
|---|------|--------|
| 1 | `requirements.txt` | Replaced by pyproject.toml |
| 2 | `app.py` | Split into src/main.py, routes/, services/ |
| 3 | `database.py` | Replaced by src/database.py |
| 4 | `models.py` | Replaced by src/models.py |
| 5 | `init_db.py` | Replaced by src/seed.py |
| 6 | `test_app.py` | Replaced by tests/test_api.py |

### Zero-change files

- `pdf_generator.py` — pure ReportLab, no framework dependency
- `templates/` — Jinja2 templates work unchanged (add `url_for` to context)
- `static/` — all JS/CSS files unchanged
- `PRD.md` — documentation

---

## Key Design Decisions

### 1. Async SQLAlchemy 2.0 with asyncpg

All models use `DeclarativeBase` instead of `db.Model`. Column definitions use `mapped_column`. Every route is `async def`. DB calls use `await`:
```python
result = await db.execute(select(Client).where(Client.id == client_id))
client = result.scalar_one_or_none()
```

### 2. Jinja2 template compat

Add `url_for` to the Jinja2 global context so existing `{{ url_for('static', filename='...') }}` calls work without changes:
```python
templates.env.globals["url_for"] = lambda name, filename=None: f"/{name}/{filename}"
```

### 3. Seed on startup (FastAPI lifespan)

`src/seed.py` provides `seed_database()` — called during FastAPI's lifespan. Only seeds if the clients table is empty. Also usable as `python -m src.seed`.

### 4. Railway PostgreSQL

Railway provides `DATABASE_URL` (postgresql://...). The config converts it to `postgresql+asyncpg://` automatically. For local dev, the .env sets a local PostgreSQL URL.

### 5. ruff config in pyproject.toml

Rules: `E`, `F`, `I`, `N`, `W`, `UP`, `ANN` (select). Applied via pre-commit hook and GitHub Actions workflow.

---

## Dependencies (pyproject.toml)

**Runtime**: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `jinja2`, `python-multipart`, `pydantic`, `pydantic-settings`, `reportlab`, `python-dotenv`

**Dev**: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `pre-commit`, `aiosqlite` (for test in-memory DB)

---

## Implementation Order

| Step | Action | Files |
|------|--------|-------|
| 1 | Create pyproject.toml with all deps + ruff config | `pyproject.toml` |
| 2 | Create src/config.py | `src/config.py` |
| 3 | Create src/database.py (async engine, get_db) | `src/database.py` |
| 4 | Create src/models.py (DeclarativeBase, mapped models) | `src/models.py` |
| 5 | Create src/seed.py (async seed function) | `src/seed.py` |
| 6 | Create src/schemas/client.py and src/schemas/report.py | `src/schemas/` |
| 7 | Create src/services/client_service.py and report_service.py | `src/services/` |
| 8 | Create src/routes/pages.py (Jinja2 routes) | `src/routes/pages.py` |
| 9 | Create src/routes/api.py (REST routes) | `src/routes/api.py` |
| 10 | Create src/main.py (FastAPI app, lifespan, template config) | `src/main.py` |
| 11 | Update .env and .env.example for PostgreSQL | `.env`, `.env.example` |
| 12 | Update Procfile for uvicorn | `Procfile` |
| 13 | Delete old files: app.py, database.py, models.py, init_db.py, requirements.txt, test_app.py | — |
| 14 | Create tests/ package with conftest.py + test_api.py | `tests/` |
| 15 | Create .pre-commit-config.yaml | `.pre-commit-config.yaml` |
| 16 | Create .github/workflows/ci.yml | `.github/workflows/ci.yml` |
| 17 | Update README.md setup instructions | `README.md` |

---

## Verification

1. Run `uv sync` — dependencies install cleanly
2. Run `ruff check src/` — no lint errors
3. Run `python -m src.seed` — seeds sample data
4. Run `uvicorn src.main:app` — app starts, API responds
5. Run `pytest tests/` — all tests pass
6. Browse `http://localhost:8000` — dashboard loads with sample clients
7. Generate a report and download PDFs
