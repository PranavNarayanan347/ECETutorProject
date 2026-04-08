from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row

from services.api.config import get_settings

logger = logging.getLogger(__name__)

_pool: psycopg.Connection | None = None


def _dsn() -> str:
    return get_settings().database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(_dsn(), row_factory=dict_row)


@contextmanager
def transactional() -> Generator[psycopg.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migrations() -> None:
    settings = get_settings()
    if not settings.database_url:
        logger.info("No DATABASE_URL configured; skipping migrations.")
        return
    try:
        with transactional() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            from pathlib import Path

            migration_dir = Path(__file__).resolve().parent.parent.parent / "infra" / "migrations"
            for sql_file in sorted(migration_dir.glob("*.sql")):
                logger.info("Running migration %s", sql_file.name)
                conn.execute(sql_file.read_text())
        logger.info("Migrations complete.")
    except Exception as exc:
        logger.warning("Migration skipped: %s", exc)
