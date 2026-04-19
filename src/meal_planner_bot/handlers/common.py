from html import escape
from datetime import date, datetime
from typing import Optional

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from meal_planner_bot.access import AccessRepository
from meal_planner_bot.dishes import Dish, DishRepository, DishSeed
from meal_planner_bot.priority_reminders import format_priority_prompt, format_schedule_text
from meal_planner_bot.settings_repository import SettingsRepository

router = Router()


def _request_access_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Запросить доступ", callback_data="access:request")],
            [InlineKeyboardButton(text="Отмена", callback_data="access:cancel")],
        ]
    )


def _admin_review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Одобрить", callback_data=f"access:approve:{user_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"access:reject:{user_id}"),
            ]
            ,
            [InlineKeyboardButton(text="Отмена", callback_data=f"access:cancel_review:{user_id}")]
        ]
    )


def _format_user_label(user: Optional[User]) -> str:
    if user is None:
        return "Неизвестный пользователь"
    parts = [user.full_name]
    if user.username:
        parts.append(f"@{user.username}")
    parts.append(f"id={user.id}")
    return " | ".join(parts)


def _has_bot_access(user_id: int, access_repo: AccessRepository, admin_user_ids: set[int]) -> bool:
    return user_id in admin_user_ids or access_repo.has_access(user_id)


def _parse_weekday(value: str) -> Optional[int]:
    normalized = value.strip().lower()
    weekday_map = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "mon": 0,
        "monday": 0,
        "понедельник": 0,
        "tue": 1,
        "tuesday": 1,
        "вторник": 1,
        "wed": 2,
        "wednesday": 2,
        "среда": 2,
        "thu": 3,
        "thursday": 3,
        "четверг": 3,
        "fri": 4,
        "friday": 4,
        "пятница": 4,
        "sat": 5,
        "saturday": 5,
        "суббота": 5,
        "sun": 6,
        "sunday": 6,
        "воскресенье": 6,
    }
    return weekday_map.get(normalized)


def _format_priority_label(priority: Optional[int]) -> str:
    priority_labels = {
        0: "совсем не нравится, не готовим больше",
        1: "не нравится, но можно приготовить",
        2: "нравится",
        3: "очень нравится",
    }
    if priority is None:
        return "не указан"
    return f"{priority} ({priority_labels.get(priority, 'неизвестно')})"


def _encode_suggestion_ids(suggestions: dict[str, Optional[Dish]]) -> Optional[str]:
    soup = suggestions.get("суп")
    main = suggestions.get("второе")
    salad = suggestions.get("салат")
    if soup is None or main is None or salad is None:
        return None
    return f"{soup.id},{main.id},{salad.id}"


def _decode_suggestion_ids(raw_value: str) -> Optional[dict[str, int]]:
    parts = raw_value.split(",")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return {
        "суп": int(parts[0]),
        "второе": int(parts[1]),
        "салат": int(parts[2]),
    }


def _suggestion_keyboard(encoded_ids: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать", callback_data=f"suggest:choose:{encoded_ids}")],
            [InlineKeyboardButton(text="Изменить", callback_data=f"suggest:change:{encoded_ids}")],
            [InlineKeyboardButton(text="Отмена", callback_data=f"suggest:close:{encoded_ids}")],
        ]
    )


def _suggestion_replace_keyboard(encoded_ids: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заменить суп", callback_data=f"suggest:replace:s:{encoded_ids}")],
            [InlineKeyboardButton(text="Заменить второе", callback_data=f"suggest:replace:m:{encoded_ids}")],
            [InlineKeyboardButton(text="Заменить салат", callback_data=f"suggest:replace:a:{encoded_ids}")],
            [InlineKeyboardButton(text="Отмена", callback_data=f"suggest:cancel:{encoded_ids}")],
        ]
    )


def _format_suggestion_text(suggestions: dict[str, Optional[Dish]]) -> str:
    headers = {
        "суп": "🍲 <b>Суп</b>",
        "второе": "🍽️ <b>Второе</b>",
        "салат": "🥗 <b>Салат</b>",
    }
    lines = ["✨ <b>Рекомендация на сегодня</b>", ""]
    for dish_type in ("суп", "второе", "салат"):
        dish = suggestions.get(dish_type)
        if dish is None:
            lines.append(f"{headers[dish_type]}")
            lines.append("- Подходящих блюд не найдено")
            lines.append("")
            continue
        lines.append(headers[dish_type])
        lines.append(f"- <b>{escape(dish.name)}</b>")
        lines.append(f"- ID: <code>{dish.id}</code>")
        lines.append(f"- Приоритет: <code>{escape(_format_priority_label(dish.priority))}</code>")
        lines.append(f"- Заказывали: <code>{dish.order_count}</code> раз")
        lines.append(f"- Последний заказ: <code>{escape(dish.last_ordered_at or 'не указан')}</code>")
        lines.append("")
    return "\n".join(lines)


def _build_slug(name: str) -> str:
    translit_map = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
        "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
        "я": "ya",
    }
    slug_chars = []
    for char in name.lower():
        if char.isascii() and char.isalnum():
            slug_chars.append(char)
        elif char in translit_map:
            slug_chars.append(translit_map[char])
        else:
            slug_chars.append("-")
    slug = "".join(slug_chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _format_dish_details(dish: Dish) -> str:
    lines = [
        f"Название: {dish.name}",
        f"ID: {dish.id}",
        f"Тип: {dish.dish_type}",
        f"Заказывали: {dish.order_count} раз",
        f"Приоритет: {_format_priority_label(dish.priority)}",
        f"Последний заказ: {dish.last_ordered_at or 'не указан'}",
        f"Не рекомендовать до: {dish.do_not_recommend_until or 'не указано'}",
    ]
    if dish.recipe_url:
        lines.append(f"Рецепт: {dish.recipe_url}")
    if dish.notes:
        lines.append(f"Комментарий: {dish.notes}")
    return "\n".join(lines)


@router.message(Command("start"))
async def start_handler(message: Message, access_repo: AccessRepository, admin_user_ids: set[int]) -> None:
    user = message.from_user
    if user is None:
        return

    if _has_bot_access(user.id, access_repo, admin_user_ids):
        await message.answer(
            "Привет! Доступ подтвержден.\n"
            "Я помогу хранить список блюд и подскажу, что можно заказать или приготовить."
        )
        return

    request = access_repo.get_request(user.id)
    if request is None:
        await message.answer(
            "Привет! Этот бот работает по заявкам.\n"
            "Нажмите кнопку ниже, чтобы отправить запрос администратору.",
            reply_markup=_request_access_keyboard(),
        )
        return

    if request.status == "pending":
        await message.answer("Ваша заявка уже отправлена и ждет подтверждения администратора.")
        return

    await message.answer(
        "Доступ пока не одобрен.\n"
        "Вы можете отправить заявку повторно.",
        reply_markup=_request_access_keyboard(),
    )


@router.message(Command("help"))
async def help_handler(message: Message, access_repo: AccessRepository, admin_user_ids: set[int]) -> None:
    user = message.from_user
    if user is None:
        return

    if _has_bot_access(user.id, access_repo, admin_user_ids):
        await message.answer(
            "Доступные команды:\n"
            "/start - начать работу с ботом\n"
            "/help - показать это сообщение\n"
            "/request_access - отправить заявку на доступ\n"
            "/whoami - показать ваш Telegram ID и статус доступа\n"
            "/dishes - показать список блюд\n"
            "/dish <id|slug|название> - показать карточку блюда\n"
            "/suggest - предложить 3 блюда: суп, второе и салат\n"
            "/add_dish <тип> | <название> | [ссылка] | [комментарий] - добавить блюдо\n"
            "/update_last_ordered <id|slug|название> | [YYYY-MM-DD] - обновить дату заказа\n"
            "/set_dishes_review_schedule [день_недели HH:MM] - показать или изменить расписание оценки заказанных блюд"
        )
        return

    await message.answer(
        "Пока у вас нет доступа к функциям бота.\n"
        "Используйте /request_access, чтобы отправить заявку администратору.\n"
        "/whoami - показать ваш Telegram ID и статус доступа"
    )


@router.message(Command("whoami"))
async def whoami_handler(
    message: Message,
    access_repo: AccessRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return

    if user.id in admin_user_ids:
        access_status = "администратор"
    elif access_repo.has_access(user.id):
        access_status = "доступ одобрен"
    else:
        request = access_repo.get_request(user.id)
        if request is None:
            access_status = "заявка не отправлена"
        elif request.status == "pending":
            access_status = "заявка на рассмотрении"
        elif request.status == "rejected":
            access_status = "заявка отклонена"
        else:
            access_status = "статус неизвестен"

    username_line = f"Username: @{user.username}" if user.username else "Username: не указан"
    await message.answer(
        f"Ваш Telegram ID: {user.id}\n"
        f"{username_line}\n"
        f"Статус доступа: {access_status}"
    )


@router.message(Command("dishes"))
async def dishes_handler(
    message: Message,
    access_repo: AccessRepository,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if not _has_bot_access(user.id, access_repo, admin_user_ids):
        await message.answer("У вас нет доступа. Используйте /request_access.")
        return

    dishes = dish_repo.list_active()
    grouped: dict[str, list[Dish]] = {}
    for dish in dishes:
        grouped.setdefault(dish.dish_type, []).append(dish)

    sections = []
    for dish_type in sorted(grouped):
        lines = [f"{dish_type.title()}:"]
        for dish in grouped[dish_type]:
            meta = []
            if dish.priority != 2:
                meta.append(f"приоритет: {_format_priority_label(dish.priority)}")
            if dish.order_count:
                meta.append(f"заказов: {dish.order_count}")
            if dish.last_ordered_at:
                meta.append(f"последний: {dish.last_ordered_at}")
            if dish.do_not_recommend_until:
                meta.append(f"пауза до: {dish.do_not_recommend_until}")
            meta_text = f" ({', '.join(meta)})" if meta else ""
            lines.append(f"{dish.id}. {dish.name}{meta_text}")
        sections.append("\n".join(lines))

    await message.answer("\n\n".join(sections))


@router.message(Command("dish"))
async def dish_handler(
    message: Message,
    command: CommandObject,
    access_repo: AccessRepository,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if not _has_bot_access(user.id, access_repo, admin_user_ids):
        await message.answer("У вас нет доступа. Используйте /request_access.")
        return

    query = (command.args or "").strip()
    if not query:
        await message.answer("Использование: /dish <id|slug|название>")
        return

    dish = dish_repo.find_one(query)
    if dish is None:
        await message.answer("Блюдо не найдено.")
        return

    await message.answer(_format_dish_details(dish))


@router.message(Command("suggest"))
async def suggest_handler(
    message: Message,
    access_repo: AccessRepository,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if not _has_bot_access(user.id, access_repo, admin_user_ids):
        await message.answer("У вас нет доступа. Используйте /request_access.")
        return

    suggestions = dish_repo.get_suggestions()
    if not any(suggestions.values()):
        await message.answer("Сейчас не получилось подобрать блюда. Проверьте справочник.")
        return
    encoded_ids = _encode_suggestion_ids(suggestions)
    reply_markup = _suggestion_keyboard(encoded_ids) if encoded_ids else None
    await message.answer(
        _format_suggestion_text(suggestions),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


@router.message(Command(commands=["set_dishes_review_schedule", "set_priority_prompt_schedule"]))
async def set_dishes_review_schedule_handler(
    message: Message,
    command: CommandObject,
    settings_repo: SettingsRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if user.id not in admin_user_ids:
        await message.answer("Менять расписание может только администратор.")
        return

    raw_args = (command.args or "").strip()
    current_schedule = settings_repo.get_priority_prompt_schedule()
    if not raw_args:
        await message.answer(
            "Текущее расписание оценки заказанных блюд:\n"
            f"{format_schedule_text(current_schedule.weekday, current_schedule.time_utc)}\n\n"
            "Изменить: /set_dishes_review_schedule пятница 14:00\n"
            "Можно использовать weekday как число 0-6, русское или английское название."
        )
        return

    parts = raw_args.split()
    if len(parts) != 2:
        await message.answer(
            "Использование: /set_dishes_review_schedule <день_недели> <HH:MM>\n"
            "Пример: /set_dishes_review_schedule пятница 14:00"
        )
        return

    weekday = _parse_weekday(parts[0])
    if weekday is None:
        await message.answer("Не удалось распознать день недели.")
        return

    try:
        datetime.strptime(parts[1], "%H:%M")
    except ValueError:
        await message.answer("Время должно быть в формате HH:MM, например 14:00.")
        return

    settings_repo.set_priority_prompt_schedule(weekday, parts[1])
    await message.answer(
        "Расписание обновлено.\n"
        f"{format_schedule_text(weekday, parts[1])}"
    )


@router.message(Command("add_dish"))
async def add_dish_handler(
    message: Message,
    command: CommandObject,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if user.id not in admin_user_ids:
        await message.answer("Добавлять блюда пока может только администратор.")
        return

    raw_args = (command.args or "").strip()
    parts = [part.strip() for part in raw_args.split("|")] if raw_args else []
    if len(parts) < 2:
        await message.answer(
            "Использование: /add_dish <тип> | <название> | [ссылка] | [комментарий]\n"
            "Пример: /add_dish салат | Теплый салат с индейкой | https://example.com | без острого"
        )
        return

    dish_type, name = parts[0], parts[1]
    recipe_url = parts[2] if len(parts) > 2 and parts[2] else None
    notes = parts[3] if len(parts) > 3 and parts[3] else None
    slug = _build_slug(name)

    existing_dish = dish_repo.find_one(slug)
    if existing_dish is not None:
        await message.answer(
            f"Блюдо уже существует.\n\n{_format_dish_details(existing_dish)}"
        )
        return

    created_dish = dish_repo.create(
        DishSeed(
            name=name,
            slug=slug,
            dish_type=dish_type,
            notes=notes,
            recipe_url=recipe_url,
        )
    )
    await message.answer(f"Блюдо добавлено.\n\n{_format_dish_details(created_dish)}")


@router.message(Command("update_last_ordered"))
async def update_last_ordered_handler(
    message: Message,
    command: CommandObject,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return
    if user.id not in admin_user_ids:
        await message.answer("Обновлять дату заказа пока может только администратор.")
        return

    raw_args = (command.args or "").strip()
    parts = [part.strip() for part in raw_args.split("|")] if raw_args else []
    if not parts or not parts[0]:
        await message.answer(
            "Использование: /update_last_ordered <id|slug|название> | [YYYY-MM-DD]\n"
            "Пример: /update_last_ordered 3 | 2026-04-19"
        )
        return

    dish = dish_repo.find_one(parts[0])
    if dish is None:
        await message.answer("Блюдо не найдено.")
        return

    ordered_at = parts[1] if len(parts) > 1 and parts[1] else date.today().isoformat()
    try:
        datetime.strptime(ordered_at, "%Y-%m-%d")
    except ValueError:
        await message.answer("Дата должна быть в формате YYYY-MM-DD, например 2026-04-19.")
        return

    updated_dish = dish_repo.update_last_ordered(dish.id, ordered_at)
    if updated_dish is None:
        await message.answer("Не удалось обновить дату заказа.")
        return

    await message.answer(
        f"Дата последнего заказа обновлена.\n\n{_format_dish_details(updated_dish)}"
    )


@router.callback_query(F.data.startswith("priority:"))
async def priority_callback_handler(
    callback: CallbackQuery,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return

    if callback.from_user.id not in admin_user_ids:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    _, action, raw_dish_id, *rest = callback.data.split(":")
    dish = dish_repo.get_by_id(int(raw_dish_id))
    if dish is None:
        await callback.answer("Блюдо не найдено.", show_alert=True)
        return

    if action == "skip":
        await callback.message.edit_text(
            f"{format_priority_prompt(dish)}\n\nИзменение приоритета отменено."
        )
        await callback.answer("Отменено")
        return

    priority = int(rest[0])
    updated_dish = dish_repo.update_priority(dish.id, priority)
    if updated_dish is None:
        await callback.answer("Не удалось обновить приоритет.", show_alert=True)
        return

    await callback.message.edit_text(
        f"{format_priority_prompt(updated_dish)}\n\nПриоритет сохранен."
    )
    await callback.answer("Приоритет обновлен")


@router.callback_query(F.data.startswith("suggest:"))
async def suggest_callback_handler(
    callback: CallbackQuery,
    access_repo: AccessRepository,
    dish_repo: DishRepository,
    admin_user_ids: set[int],
) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return

    if not _has_bot_access(callback.from_user.id, access_repo, admin_user_ids):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    _, action, *rest = callback.data.split(":")
    if not rest:
        await callback.answer()
        return

    if action == "choose":
        decoded_ids = _decode_suggestion_ids(rest[0])
        if decoded_ids is None:
            await callback.answer("Не удалось разобрать выбор.", show_alert=True)
            return

        ordered_at = date.today().isoformat()
        updated_dishes = []
        for dish_id in decoded_ids.values():
            updated_dish = dish_repo.update_last_ordered(dish_id, ordered_at)
            if updated_dish is not None:
                updated_dishes.append(updated_dish.name)

        updated_suggestions = {
            "суп": dish_repo.get_by_id(decoded_ids["суп"]),
            "второе": dish_repo.get_by_id(decoded_ids["второе"]),
            "салат": dish_repo.get_by_id(decoded_ids["салат"]),
        }

        await callback.message.edit_text(
            f"{_format_suggestion_text(updated_suggestions)}\n\n"
            f"✅ <b>Вы выбрали этот набор.</b>\n"
            f"Дата заказа обновлена: <code>{ordered_at}</code>\n"
            f"Зафиксированы блюда: {escape(', '.join(updated_dishes))}.",
            parse_mode=ParseMode.HTML,
        )
        await callback.answer("Набор выбран")
        return

    if action == "change":
        decoded_ids = _decode_suggestion_ids(rest[0])
        if decoded_ids is None:
            await callback.answer("Не удалось разобрать набор.", show_alert=True)
            return
        await callback.message.edit_reply_markup(reply_markup=_suggestion_replace_keyboard(rest[0]))
        await callback.answer("Выберите, что заменить")
        return

    if action == "close":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Отменено")
        return

    if action == "cancel":
        decoded_ids = _decode_suggestion_ids(rest[0])
        if decoded_ids is None:
            await callback.answer("Не удалось разобрать набор.", show_alert=True)
            return
        await callback.message.edit_reply_markup(reply_markup=_suggestion_keyboard(rest[0]))
        await callback.answer("Изменение отменено")
        return

    if action == "replace" and len(rest) == 2:
        type_code = rest[0]
        encoded_ids = rest[1]
        decoded_ids = _decode_suggestion_ids(encoded_ids)
        if decoded_ids is None:
            await callback.answer("Не удалось разобрать набор.", show_alert=True)
            return

        dish_type_map = {"s": "суп", "m": "второе", "a": "салат"}
        dish_type = dish_type_map.get(type_code)
        if dish_type is None:
            await callback.answer("Неизвестный тип блюда.", show_alert=True)
            return

        excluded_id = decoded_ids[dish_type]
        new_dish = dish_repo.get_suggestion_for_type(dish_type, excluded_ids={excluded_id})
        if new_dish is None:
            await callback.answer("Не нашел другой вариант для замены.", show_alert=True)
            return

        decoded_ids[dish_type] = new_dish.id
        updated_suggestions = {
            "суп": dish_repo.get_by_id(decoded_ids["суп"]),
            "второе": dish_repo.get_by_id(decoded_ids["второе"]),
            "салат": dish_repo.get_by_id(decoded_ids["салат"]),
        }
        new_encoded_ids = _encode_suggestion_ids(updated_suggestions)
        if new_encoded_ids is None:
            await callback.answer("Не удалось собрать новый набор.", show_alert=True)
            return

        await callback.message.edit_text(
            _format_suggestion_text(updated_suggestions),
            reply_markup=_suggestion_keyboard(new_encoded_ids),
            parse_mode=ParseMode.HTML,
        )
        await callback.answer("Блюдо заменено")
        return

    await callback.answer()


@router.message(Command("request_access"))
async def request_access_handler(
    message: Message,
    access_repo: AccessRepository,
    admin_user_ids: set[int],
) -> None:
    user = message.from_user
    if user is None:
        return

    if user.id in admin_user_ids or access_repo.has_access(user.id):
        await message.answer("У вас уже есть доступ к боту.")
        return

    request_state = access_repo.create_or_refresh_request(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

    if request_state == "pending":
        await message.answer("Ваша заявка уже находится на рассмотрении.")
        return

    await message.answer("Заявка отправлена администратору. Я напишу, когда доступ будет одобрен.")

    admin_text = (
        "Новая заявка на доступ.\n"
        f"Пользователь: {_format_user_label(user)}"
    )
    for admin_user_id in admin_user_ids:
        await message.bot.send_message(
            admin_user_id,
            admin_text,
            reply_markup=_admin_review_keyboard(user.id),
        )


@router.callback_query(F.data == "access:request")
async def request_access_callback(
    callback: CallbackQuery,
    access_repo: AccessRepository,
    admin_user_ids: set[int],
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    request_state = access_repo.create_or_refresh_request(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )

    if request_state == "approved":
        await callback.message.answer("У вас уже есть доступ к боту.")
    elif request_state == "pending":
        await callback.message.answer("Ваша заявка уже находится на рассмотрении.")
    else:
        await callback.message.answer("Заявка отправлена администратору. Ожидайте подтверждения.")
        user_label = _format_user_label(callback.from_user)
        for admin_user_id in admin_user_ids:
            await callback.bot.send_message(
                admin_user_id,
                f"Новая заявка на доступ.\nПользователь: {user_label}",
                reply_markup=_admin_review_keyboard(callback.from_user.id),
            )

    await callback.answer()


@router.callback_query(F.data == "access:cancel")
async def cancel_access_callback(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Отменено")


@router.callback_query(F.data.startswith("access:"))
async def review_access_callback(
    callback: CallbackQuery,
    access_repo: AccessRepository,
    admin_user_ids: set[int],
) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return

    if callback.from_user.id not in admin_user_ids:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Не удалось разобрать действие.", show_alert=True)
        return

    _, action, raw_user_id = parts
    if action == "request":
        await callback.answer()
        return
    if action == "cancel_review":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Отменено")
        return

    target_user_id = int(raw_user_id)
    request = access_repo.get_request(target_user_id)
    if request is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    new_status = "approved" if action == "approve" else "rejected"
    updated_request = access_repo.review_request(target_user_id, callback.from_user.id, new_status)
    if updated_request is None:
        await callback.answer("Не удалось обновить заявку.", show_alert=True)
        return

    status_text = "одобрена" if new_status == "approved" else "отклонена"
    user_text = (
        f"Заявка {status_text}: "
        f"{escape(updated_request.full_name)}"
        f"{' (@' + escape(updated_request.username) + ')' if updated_request.username else ''} "
        f"[id={updated_request.user_id}]"
    )
    await callback.message.edit_text(user_text)

    if new_status == "approved":
        await callback.bot.send_message(
            target_user_id,
            "Ваша заявка одобрена. Теперь вы можете пользоваться ботом.",
        )
    else:
        await callback.bot.send_message(
            target_user_id,
            "Ваша заявка отклонена. При необходимости вы можете отправить ее повторно позже.",
        )

    await callback.answer("Готово")
