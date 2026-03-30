"""Lightweight schema migrations for SQLite.

SQLAlchemy's ``create_all`` only creates missing *tables*; it never adds
columns to an existing table.  This module fills that gap with idempotent
ALTER TABLE statements so the app can evolve its schema without a full
migration framework.
"""

import logging

from sqlalchemy import Inspector, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Each entry is (table, column, column_definition).
_PENDING_COLUMNS: list[tuple[str, str, str]] = [
    ("sessions", "summary", "TEXT"),
    ("sessions", "memory_config_json", "TEXT"),
]


def run_migrations(engine: Engine) -> None:
    """Add any columns that exist in the ORM models but not yet in the DB."""
    inspector = Inspector.from_engine(engine)
    with engine.begin() as conn:
        for table, column, definition in _PENDING_COLUMNS:
            existing = {col["name"] for col in inspector.get_columns(table)}
            if column not in existing:
                conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                )
                logger.info("migration: added column %s.%s", table, column)
