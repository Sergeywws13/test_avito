from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from src.models.user import User
from src.database.db import async_session

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


@start_router.message(Command("delete_account"))
async def delete_account(message: Message):
    user_id = message.from_user.id
    async with async_session() as session:
        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
            await message.answer("Аккаунт удален.")
        else:
            await message.answer("Аккаунт не найден.")