from html import escape
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from meal_planner_bot.access import AccessRepository

router = Router()


def _request_access_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Запросить доступ", callback_data="access:request")]
        ]
    )


def _admin_review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Одобрить", callback_data=f"access:approve:{user_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"access:reject:{user_id}"),
            ]
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


@router.message(Command("start"))
async def start_handler(message: Message, access_repo: AccessRepository, admin_user_ids: set[int]) -> None:
    user = message.from_user
    if user is None:
        return

    if user.id in admin_user_ids or access_repo.has_access(user.id):
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

    if user.id in admin_user_ids or access_repo.has_access(user.id):
        await message.answer(
            "Доступные команды:\n"
            "/start - начать работу с ботом\n"
            "/help - показать это сообщение\n"
            "/request_access - отправить заявку на доступ\n"
            "/whoami - показать ваш Telegram ID и статус доступа"
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

    _, action, raw_user_id = callback.data.split(":")
    if action == "request":
        await callback.answer()
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
