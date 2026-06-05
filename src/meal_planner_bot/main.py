from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from meal_planner_bot.access import AccessRepository
from meal_planner_bot.config import load_settings
from meal_planner_bot.database import init_database
from meal_planner_bot.dishes import DishRepository
from meal_planner_bot.handlers import setup_routers


async def setup_bot_commands(bot: Bot, admin_user_ids: set[int]) -> None:
    common_commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Показать список команд"),
        BotCommand(command="request_access", description="Отправить заявку на доступ"),
        BotCommand(command="dishes", description="Показать список блюд"),
        BotCommand(command="dish", description="Показать карточку блюда"),
        BotCommand(command="suggest", description="Подобрать 3 блюда"),
    ]
    admin_commands = [
        *common_commands,
        BotCommand(command="whoami", description="Показать ваш Telegram ID"),
        BotCommand(command="add_dish", description="Добавить новое блюдо"),
        BotCommand(command="update_last_ordered", description="Обновить дату последнего заказа"),
    ]
    await bot.set_my_commands(common_commands, scope=BotCommandScopeDefault())
    await bot.set_my_commands(common_commands, scope=BotCommandScopeAllPrivateChats())
    for admin_user_id in admin_user_ids:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_user_id))


async def run_bot() -> None:
    settings = load_settings()
    init_database(settings.database_path)
    access_repo = AccessRepository(settings.database_path)
    dish_repo = DishRepository(settings.database_path)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(token=settings.bot_token)
    await setup_bot_commands(bot, settings.admin_user_ids)
    dispatcher = Dispatcher()
    dispatcher["access_repo"] = access_repo
    dispatcher["dish_repo"] = dish_repo
    dispatcher["admin_user_ids"] = settings.admin_user_ids
    dispatcher.include_router(setup_routers())

    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())
