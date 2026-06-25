from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def get_database_url() -> str:
    """Return the async database connection string.

    - PostgreSQL from Railway (DATABASE_URL): automatically converts
      ``postgresql://`` to ``postgresql+asyncpg://``.
    - SQLite for local development: any ``sqlite://`` URL is transparently
      converted to ``sqlite+aiosqlite://`` for the aiosqlite driver.
    """
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/financial_portal",
    )
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and "+aiosqlite" not in url:
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def get_secret_key() -> str:
    return os.environ.get("SECRET_KEY", "dev-secret-key")


def get_pdf_output_dir() -> str:
    return os.environ.get("PDF_OUTPUT_DIR", str(BASE_DIR / "generated_pdfs"))
