from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str
    admin_user_ids: set[int]
    database_path: Path


def _parse_admin_user_ids(raw_value: str) -> set[int]:
    admin_ids = set()
    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value:
            continue
        if not value.isdigit():
            raise ValueError("ADMIN_USER_IDS must contain only Telegram numeric user IDs.")
        admin_ids.add(int(value))
    return admin_ids


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set. Create a .env file based on .env.example.")

    admin_user_ids = _parse_admin_user_ids(os.getenv("ADMIN_USER_IDS", ""))
    if not admin_user_ids:
        raise ValueError("ADMIN_USER_IDS is not set. Add at least one admin Telegram user ID.")

    database_path = Path(os.getenv("DATABASE_PATH", "data/meal_planner_bot.db"))

    return Settings(
        bot_token=bot_token,
        admin_user_ids=admin_user_ids,
        database_path=database_path,
    )
