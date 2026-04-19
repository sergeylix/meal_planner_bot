from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional


@dataclass(frozen=True)
class PriorityPromptSchedule:
    weekday: int
    time_utc: str
    last_run_at: Optional[str] = None


class SettingsRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return default
        return str(row["value"])

    def set_value(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO bot_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            connection.commit()

    def get_priority_prompt_schedule(self) -> PriorityPromptSchedule:
        weekday = int(self.get_value("priority_prompt_weekday", "4") or "4")
        time_utc = self.get_value("priority_prompt_time_utc", "14:00") or "14:00"
        last_run_at = self.get_value("priority_prompt_last_run_at")
        return PriorityPromptSchedule(
            weekday=weekday,
            time_utc=time_utc,
            last_run_at=last_run_at,
        )

    def set_priority_prompt_schedule(self, weekday: int, time_utc: str) -> None:
        self.set_value("priority_prompt_weekday", str(weekday))
        self.set_value("priority_prompt_time_utc", time_utc)

    def set_priority_prompt_last_run_at(self, value: str) -> None:
        self.set_value("priority_prompt_last_run_at", value)
