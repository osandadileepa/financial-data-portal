from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import BASE_DIR, get_secret_key
from src.routes.api import router as api_router
from src.routes.pages import router as pages_router
from src.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed sample data on startup."""
    await seed_database()
    yield


app = FastAPI(
    title="AW Client Report Portal",
    version="2.0.0",
    lifespan=lifespan,
)

# Mount static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Jinja2 templates with a shim url_for so Flask-style templates work unchanged
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _url_for(name: str, **kwargs) -> str:
    """Shim for Flask's url_for('static', filename='...') in templates."""
    if name == "static":
        filename = kwargs.get("filename", "")
        return f"/static/{filename}"
    return f"/{name}"


templates.env.globals["url_for"] = _url_for

# Register routers
app.include_router(pages_router)
app.include_router(api_router, prefix="/api")


# ── Error handlers ────────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, str) else exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
