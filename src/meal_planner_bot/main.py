import asyncio
import logging

from aiogram import Bot, Dispatcher

from meal_planner_bot.config import load_settings
from meal_planner_bot.handlers import setup_routers


async def run_bot() -> None:
    settings = load_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(setup_routers())

    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())
