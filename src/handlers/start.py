from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from src.models.user import User
from src.database.db import async_session

start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: Message):
    text = "Привет! Я бот для работы с Avito. Чтобы начать пользоваться мной, вам нужно зарегистрироваться.\n" \
    "Посмотрите дополнительную информацию по команде /info, чтобы ознакомиться с работой бота!"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Начать регистрацию", callback_data="register")
            ]
        ]
    )
    await message.answer(text, reply_markup=keyboard)


class DeleteAccountStates(StatesGroup):
    waiting_for_confirmation = State()

@start_router.message(Command("delete_account"))
async def delete_account(message: Message, state: FSMContext):
    await message.answer("Вы уверены, что хотите удалить свой аккаунт? (да/нет)")
    await state.set_state(DeleteAccountStates.waiting_for_confirmation)

@start_router.message(DeleteAccountStates.waiting_for_confirmation)
async def process_delete_account(message: Message, state: FSMContext):
    if message.text.lower() == "да":
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
    elif message.text.lower() == "нет":
        await message.answer("Удаление аккаунта отменено.")
    else:
        await message.answer("Неправильный ответ. Пожалуйста, введите да или нет.")
    await state.clear()


@start_router.message(Command("info"))
async def info_command(message: Message):
    text = """
Добро пожаловать в бот для работы с Avito! 🚀

Этот бот предназначен для упрощения взаимодействия с Avito и предоставления дополнительных функций для пользователей.

Основные команды:
* /start - начать работу с ботом 💻
* /register - зарегистрироваться в боте 📝
* /delete_account - удалить свой аккаунт ❌
* /info - получить информацию о боте 🤔

Функции бота:
* Получение сообщений из Avito 📨 - получайте сообщения из Avito прямо в Telegram!
* Отправка ответов на сообщения из Avito 📨 - отвечайте на сообщения из Avito прямо из Telegram!
* Управление аккаунтом и настройками бота 🔧 - управляйте своим аккаунтом и настройками бота с помощью простых команд!

Как начать:
1. Нажмите на команду /start для начала работы с ботом.
2. Нажмите на команду /register для регистрации в боте.
3. Введите свои данные для регистрации.
4. Нажмите на команду /info для получения информации о боте.
"""
    await message.answer(text)