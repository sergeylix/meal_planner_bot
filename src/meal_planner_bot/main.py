from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from meal_planner_bot.access import AccessRepository
from meal_planner_bot.config import load_settings
from meal_planner_bot.database import init_database
from meal_planner_bot.dishes import DishRepository
from meal_planner_bot.handlers import setup_routers
from meal_planner_bot.priority_reminders import PriorityReminderService
from meal_planner_bot.settings_repository import SettingsRepository


async def setup_bot_commands(bot: Bot) -> None:
    common_commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Показать список команд"),
        BotCommand(command="request_access", description="Отправить заявку на доступ"),
        BotCommand(command="dishes", description="Показать список блюд"),
        BotCommand(command="dish", description="Показать карточку блюда"),
        BotCommand(command="suggest", description="Подобрать 3 блюда"),
    ]
    await bot.set_my_commands(common_commands, scope=BotCommandScopeAllPrivateChats())


async def run_bot() -> None:
    settings = load_settings()
    init_database(settings.database_path)
    access_repo = AccessRepository(settings.database_path)
    dish_repo = DishRepository(settings.database_path)
    settings_repo = SettingsRepository(settings.database_path)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    await setup_bot_commands(bot)
    reminder_service = PriorityReminderService(
        bot=bot,
        dish_repo=dish_repo,
        settings_repo=settings_repo,
        admin_user_ids=settings.admin_user_ids,
    )
    reminder_task = asyncio.create_task(reminder_service.run())
    dispatcher = Dispatcher()
    dispatcher["access_repo"] = access_repo
    dispatcher["dish_repo"] = dish_repo
    dispatcher["settings_repo"] = settings_repo
    dispatcher["admin_user_ids"] = settings.admin_user_ids
    dispatcher.include_router(setup_routers())

    try:
        await dispatcher.start_polling(bot)
    finally:
        reminder_task.cancel()
        await asyncio.gather(reminder_task, return_exceptions=True)


def main() -> None:
    asyncio.run(run_bot())
