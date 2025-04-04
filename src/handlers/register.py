from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from src.handlers.start import delete_account
from src.models.user import User
from src.database.db import async_session
from src.services.user_service import get_or_create_user
from src.services.avito_api import get_access_token

register_router = Router()

class AuthStates(StatesGroup):
    waiting_for_client_id = State()
    waiting_for_client_secret = State()
    waiting_for_chat_id = State()  # Новое состояние для ожидания ID чата
    waiting_for_reply = State() 

@register_router.message(Command("register"))
async def start_command(message: Message, state: FSMContext):
    await message.answer("Введите ваш client_id:")
    await state.set_state(AuthStates.waiting_for_client_id)

@register_router.callback_query()
async def start_register(callback: CallbackQuery, state: FSMContext):
    if callback.data == "register":
        await callback.answer()
        await callback.message.answer("Введите ваш client_id:")
        await state.set_state(AuthStates.waiting_for_client_id)
    elif callback.data == "delete_account":
        await delete_account(callback.message)

@register_router.message(AuthStates.waiting_for_client_id)
async def process_client_id(message: Message, state: FSMContext):
    await state.update_data(client_id=message.text)
    await message.answer("Введите ваш client_secret:")
    await state.set_state(AuthStates.waiting_for_client_secret)

@register_router.message(AuthStates.waiting_for_client_secret)
async def process_client_secret(message: Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get("client_id")
    client_secret = message.text

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, client_id, client_secret)
        user.telegram_chat_id = message.chat.id  # Сохраняем chat_id в базе данных
        await session.commit()

        # Получаем access_token и сохраняем его в состоянии
        access_token = await get_access_token(client_id, client_secret)
        await state.update_data(access_token=access_token, user_id=user.user_id)

    await message.answer("Данные успешно сохранены!")
    await state.clear()


