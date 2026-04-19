from __future__ import annotations

from pathlib import Path
import sqlite3


def _ensure_column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_columns = {column[1] for column in columns}
    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS access_requests (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
                requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                dish_type TEXT NOT NULL,
                notes TEXT,
                recipe_url TEXT,
                last_ordered_at TEXT,
                order_count INTEGER NOT NULL DEFAULT 0,
                do_not_recommend_until TEXT,
                priority INTEGER NOT NULL DEFAULT 2 CHECK(priority IN (0, 1, 2, 3)),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        _ensure_column_exists(connection, "dishes", "order_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column_exists(connection, "dishes", "do_not_recommend_until", "TEXT")
        _ensure_column_exists(connection, "dishes", "priority", "INTEGER NOT NULL DEFAULT 2")
        connection.execute(
            """
            UPDATE dishes
            SET priority = 2
            WHERE priority IS NULL
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO bot_settings (key, value)
            VALUES
                ('priority_prompt_weekday', '4'),
                ('priority_prompt_time_utc', '14:00')
            """
        )
        connection.commit()
