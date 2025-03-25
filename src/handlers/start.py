from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.database.db import async_session
from src.services.user_service import get_or_create_user
from src.services.avito_api import get_access_token

start_router = Router()

class AuthStates(StatesGroup):
    waiting_for_client_id = State()
    waiting_for_client_secret = State()

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

    await message.answer("Данные успешно сохранены!")
    await state.clear()


    
