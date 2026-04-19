from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from meal_planner_bot.dishes import Dish, DishRepository
from meal_planner_bot.settings_repository import SettingsRepository

LOGGER = logging.getLogger(__name__)

WEEKDAY_LABELS = {
    0: "понедельник",
    1: "вторник",
    2: "среду",
    3: "четверг",
    4: "пятницу",
    5: "субботу",
    6: "воскресенье",
}


def format_priority_label(priority: int) -> str:
    labels = {
        0: "совсем не нравится, не готовим больше",
        1: "не нравится, но можно приготовить",
        2: "нравится",
        3: "очень нравится",
    }
    return f"{priority} ({labels.get(priority, 'неизвестно')})"


def build_priority_keyboard(dish_id: int) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="0", callback_data=f"priority:set:{dish_id}:0"),
        InlineKeyboardButton(text="1", callback_data=f"priority:set:{dish_id}:1"),
        InlineKeyboardButton(text="2", callback_data=f"priority:set:{dish_id}:2"),
        InlineKeyboardButton(text="3", callback_data=f"priority:set:{dish_id}:3"),
    ]
    cancel = InlineKeyboardButton(text="Отмена", callback_data=f"priority:skip:{dish_id}")
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [cancel]])


def format_schedule_text(weekday: int, time_utc: str) -> str:
    weekday_label = WEEKDAY_LABELS.get(weekday, str(weekday))
    return f"Каждую {weekday_label} в {time_utc} UTC"


def format_priority_prompt(dish: Dish) -> str:
    lines = [
        "Нужно обновить приоритет блюда из последнего заказа.",
        "",
        f"Название: {dish.name}",
        f"ID: {dish.id}",
        f"Тип: {dish.dish_type}",
        f"Заказывали: {dish.order_count} раз",
        f"Текущий приоритет: {format_priority_label(dish.priority)}",
        f"Последний заказ: {dish.last_ordered_at or 'не указан'}",
        f"Не рекомендовать до: {dish.do_not_recommend_until or 'не указано'}",
    ]
    if dish.recipe_url:
        lines.append(f"Рецепт: {dish.recipe_url}")
    if dish.notes:
        lines.append(f"Комментарий: {dish.notes}")
    return "\n".join(lines)


class PriorityReminderService:
    def __init__(
        self,
        bot: Bot,
        dish_repo: DishRepository,
        settings_repo: SettingsRepository,
        admin_user_ids: set[int],
    ):
        self.bot = bot
        self.dish_repo = dish_repo
        self.settings_repo = settings_repo
        self.admin_user_ids = admin_user_ids

    async def run(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Priority reminder scheduler failed")
            await asyncio.sleep(60)

    async def _tick(self) -> None:
        schedule = self.settings_repo.get_priority_prompt_schedule()
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        hour, minute = [int(part) for part in schedule.time_utc.split(":")]
        if now.weekday() != schedule.weekday or now.hour != hour or now.minute != minute:
            return

        scheduled_slot = now.isoformat()
        if schedule.last_run_at == scheduled_slot:
            return

        dishes = self.dish_repo.get_latest_ordered_dishes()
        if not dishes:
            self.settings_repo.set_priority_prompt_last_run_at(scheduled_slot)
            return

        for admin_user_id in self.admin_user_ids:
            for dish in dishes:
                await self.bot.send_message(
                    admin_user_id,
                    format_priority_prompt(dish),
                    reply_markup=build_priority_keyboard(dish.id),
                )

        self.settings_repo.set_priority_prompt_last_run_at(scheduled_slot)
