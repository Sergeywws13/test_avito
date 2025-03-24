import asyncio
from aiogram import types, Router
from aiogram.filters import Command
from sqlalchemy import select
from src.models.user import User
from src.services.avito_api import get_access_token, get_self_info
from src.services.message_service import fetch_and_send_messages
from src.database.db import async_session

check_router = Router()

@check_router.message(Command("check_messages"))
async def check_messages_command(message: types.Message):
    """
    Обработчик команды /check_messages.
    """
    async with async_session() as session:
        user = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = user.scalar_one_or_none()
        if user:
            access_token = get_access_token(user.client_id, user.client_secret)
            if access_token:
                self_info = get_self_info(access_token)
                user_id = self_info["id"]
                await fetch_and_send_messages(message.bot, access_token, user_id)
                await message.answer("Сообщения успешно обновлены!")
            else:
                await message.answer("Не удалось получить access token.")
        else:
            await message.answer("Пользователь не найден в базе данных.")
            