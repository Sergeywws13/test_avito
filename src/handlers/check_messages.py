from aiogram import types, Router
from sqlalchemy import select
from src.models.user import User
from src.services.avito_api import get_access_token, send_message
from src.services.message_service import fetch_and_send_messages, handle_telegram_message
from src.database.db import async_session

check_router = Router()

@check_router.message()
async def handle_incoming_message(message: types.Message):
    """
    Обработчик для всех входящих сообщений от менеджера.
    """
    async with async_session() as session:
        user = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = user.scalar_one_or_none()
        if user:
            access_token = await get_access_token(user.client_id, user.client_secret)
            if access_token:
                # Получаем chat_id, на который нужно отправить ответ
                chat_id = message.chat.id  # Или используйте другой способ получения chat_id

                # Отправляем ответ в API Авито
                response = await send_message(access_token, user.user_id, chat_id, message.text)
                if response:
                    await message.reply("Ваш ответ отправлен.")
                else:
                    await message.reply("Произошла ошибка при отправке ответа.")
            else:
                await message.answer("Не удалось получить access token.")
        else:
            await message.answer("Пользователь не найден в базе данных.")
            