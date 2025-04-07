import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.handlers.start import delete_account
from src.database.db import async_session
from src.services.user_service import get_or_create_user
from src.services.avito_api import get_access_token, get_self_info

register_router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        access_token = await get_access_token(client_id, client_secret)
        if access_token:
            self_info = await get_self_info(access_token)
            if self_info and "id" in self_info:
                user.avito_user_id = str(self_info["id"])
                logger.info(f"Сохранен avito_user_id: {user.avito_user_id}")
            else:
                await message.answer("❌ Не удалось получить ID пользователя Avito")
                return
        else:
            await message.answer("❌ Не удалось получить токен доступа")
            return
        user.telegram_chat_id = message.chat.id
        await session.commit()

    await message.answer("✅ Данные успешно сохранены!")
    await state.clear()
    