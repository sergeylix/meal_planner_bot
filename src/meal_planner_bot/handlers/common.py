from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я бот meal_planner_bot.\n"
        "Я помогу хранить список блюд и подскажу, что можно заказать или приготовить."
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start - начать работу с ботом\n"
        "/help - показать это сообщение"
    )
