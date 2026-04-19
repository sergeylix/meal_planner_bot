from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional


@dataclass
class AccessRequest:
    user_id: int
    username: Optional[str]
    full_name: str
    status: str
    requested_at: str
    updated_at: str
    reviewed_by: Optional[int]


class AccessRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_request(self, user_id: int) -> Optional[AccessRequest]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, username, full_name, status, requested_at, updated_at, reviewed_by
                FROM access_requests
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return AccessRequest(**dict(row))

    def has_access(self, user_id: int) -> bool:
        request = self.get_request(user_id)
        return request is not None and request.status == "approved"

    def create_or_refresh_request(self, user_id: int, username: Optional[str], full_name: str) -> str:
        existing_request = self.get_request(user_id)

        with self._connect() as connection:
            if existing_request is None:
                connection.execute(
                    """
                    INSERT INTO access_requests (user_id, username, full_name, status)
                    VALUES (?, ?, ?, 'pending')
                    """,
                    (user_id, username, full_name),
                )
                connection.commit()
                return "created"

            if existing_request.status == "approved":
                return "approved"

            connection.execute(
                """
                UPDATE access_requests
                SET username = ?, full_name = ?, status = 'pending',
                    updated_at = CURRENT_TIMESTAMP, reviewed_by = NULL
                WHERE user_id = ?
                """,
                (username, full_name, user_id),
            )
            connection.commit()

        return "resent" if existing_request.status == "rejected" else "pending"

    def review_request(self, user_id: int, reviewed_by: int, new_status: str) -> Optional[AccessRequest]:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE access_requests
                SET status = ?, updated_at = CURRENT_TIMESTAMP, reviewed_by = ?
                WHERE user_id = ?
                """,
                (new_status, reviewed_by, user_id),
            )
            connection.commit()

        return self.get_request(user_id)
