from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: Message):
    text = "Привет! Я бот для работы с Avito. Чтобы начать пользоваться мной, вам нужно зарегистрироваться."
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Начать регистрацию", callback_data="register")
            ]
        ]
    )
    await message.answer(text, reply_markup=keyboard)
