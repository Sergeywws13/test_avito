from aiogram import types, Router
from sqlalchemy import select
from src.services.avito_api import get_access_token, get_chats, get_self_info, send_message
from src.database.db import async_session
from src.models.user import User

check_router = Router()

# Обработчик для получения входящих сообщений
@check_router.message()
async def handle_incoming_message(message: types.Message):
    # Проверяем, является ли сообщение ответом на другое сообщение
    if message.reply_to_message:
        # Если это ответ на сообщение, вызываем функцию handle_incoming_reply
        await handle_incoming_reply(message)
    else:
        # Если это не ответ на сообщение, сохраняем информацию о сообщении
        user_id = message.from_user.id
        message_id = message.message_id  # ID сообщения Telegram

        # Отправляем сообщение пользователю с просьбой ответить
        await message.answer("Пожалуйста, ответьте на это сообщение.")

        # Сохраняем ID сообщения и ID пользователя в контексте (если нужно)
        # Здесь вы можете сохранить эти данные в базе данных или в другом месте, если это необходимо


async def handle_incoming_reply(message: types.Message):
    # Получаем данные о сообщении, на которое нужно ответить
    user_id = message.from_user.id
    message_id = message.reply_to_message.message_id  # ID сообщения, на которое отвечаем
    reply_to_message_id = message.reply_to_message.message_id  # ID сообщения, на которое отвечаем

    # Получаем информацию о пользователе из базы данных
    async with async_session() as session:
        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one_or_none()

    if user:
        # Получаем access_token для отправки сообщения
        access_token = await get_access_token(user.client_id, user.client_secret)

        if access_token:
            # Получаем информацию о текущем пользователе
            self_info = await get_self_info(access_token)
            avito_user_id = self_info["id"]

            # Получаем список чатов
            chats = await get_chats(access_token, avito_user_id)
            for chat in chats["chats"]:
                avito_chat_id = chat["id"]
                break

            # Отправляем сообщение
            response = await send_message(access_token, avito_user_id, avito_chat_id, message.text)

            if response:
                await message.reply("Ваш ответ отправлен.")
            else:
                await message.reply("Не удалось отправить ответ.")
        else:
            await message.reply("Не удалось получить access token.")
    else:
        await message.reply("Пользователь не найден в базе данных.")