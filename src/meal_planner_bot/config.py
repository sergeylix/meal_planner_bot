from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set. Create a .env file based on .env.example.")

    return Settings(bot_token=bot_token)
