"""Safe SQLite migration helpers for legacy databases."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _sqlite_path_from_uri(database_uri: str) -> Path:
    if not database_uri.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// URIs are supported by this migration helper")
    return Path(database_uri.replace("sqlite:///", "", 1))


def ensure_user_role_columns(database_uri: str) -> None:
    """Add legacy role columns when the database was created before the model update."""

    database_path = _sqlite_path_from_uri(database_uri)
    if not database_path.exists():
        return

    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "is_advisor" not in existing_columns:
            connection.execute("ALTER TABLE users ADD COLUMN is_advisor BOOLEAN NOT NULL DEFAULT 0")

        connection.commit()
