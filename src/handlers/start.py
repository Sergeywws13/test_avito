from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from src.models.user import User
from src.database.db import async_session
from src.services.user_service import get_or_create_user
from src.services.avito_api import get_access_token

start_router = Router()

class AuthStates(StatesGroup):
    waiting_for_client_id = State()
    waiting_for_client_secret = State()
    waiting_for_chat_id = State()  # Новое состояние для ожидания ID чата

@start_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await message.answer("Введите ваш client_id:")
    await state.set_state(AuthStates.waiting_for_client_id)

@start_router.message(AuthStates.waiting_for_client_id)
async def process_client_id(message: Message, state: FSMContext):
    await state.update_data(client_id=message.text)
    await message.answer("Введите ваш client_secret:")
    await state.set_state(AuthStates.waiting_for_client_secret)

@start_router.message(AuthStates.waiting_for_client_secret)
async def process_client_secret(message: Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    client_secret = message.text

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, client_id, client_secret)
        await session.commit()

        # Получаем access_token и сохраняем его в состоянии
        access_token = await get_access_token(client_id, client_secret)
        await state.update_data(access_token=access_token, user_id=user.user_id)

    await message.answer("Данные успешно сохранены! Теперь вы можете отправить сообщение, чтобы сохранить ID чата.")
    await state.set_state(AuthStates.waiting_for_chat_id)  # Переход к ожиданию ID чата

@start_router.message(AuthStates.waiting_for_chat_id)
async def save_chat_id(message: Message, state: FSMContext):
    chat_id = message.chat.id
    async with async_session() as session:
        user = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = user.scalar_one_or_none()
        if user:
            user.telegram_chat_id = chat_id
            await session.commit()
    await message.answer(f"Ваш ID чата сохранен: {chat_id}")
    await state.clear()  # Очистка состояния после сохранения ID чата

@start_router.message()
async def handle_unexpected_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AuthStates.waiting_for_client_id.state:
        await message.answer("Пожалуйста, введите ваш client_id.")
    elif current_state == AuthStates.waiting_for_client_secret.state:
        await message.answer("Пожалуйста, введите ваш client_secret.")
    elif current_state == AuthStates.waiting_for_chat_id.state:
        await message.answer("Пожалуйста, отправьте любое сообщение, чтобы сохранить ID чата.")
    else:
        await message.answer("Неизвестная команда. Пожалуйста, используйте /start для начала.")
