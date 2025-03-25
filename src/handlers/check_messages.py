from aiogram import types, Router
from src.services.avito_api import get_access_token, send_reply_to_message
from src.services.user_service import get_or_create_user
from src.database.db import async_session
from src.models.user import User

check_router = Router()

# Обработчик для получения входящих сообщений
@check_router.message()
async def handle_incoming_message(message: types.Message):
    # Сохраняем информацию о сообщении
    user_id = message.from_user.id
    message_id = message.message_id  # ID сообщения Telegram

    # Отправляем сообщение пользователю с просьбой ответить
    await message.answer("Пожалуйста, ответьте на это сообщение.")

    # Сохраняем ID сообщения и ID пользователя в контексте (если нужно)
    # Здесь вы можете сохранить эти данные в базе данных или в другом месте, если это необходимо

# Обработчик для ответов на сообщения
@check_router.message()
async def handle_incoming_reply(message: types.Message):
    # Получаем данные о сообщении, на которое нужно ответить
    user_id = message.from_user.id
    message_id = message.reply_to_message.message_id  # ID сообщения, на которое отвечаем

    # Получаем информацию о пользователе из базы данных
    async with async_session() as session:
        user = await get_or_create_user(session, user_id)

    # Получаем access_token для отправки сообщения
    access_token = await get_access_token(user.client_id, user.client_secret)

    if not access_token:
        await message.reply("Не удалось получить access token.")
        return

    # Отправляем ответ на сообщение через API Avito
    response = await send_reply_to_message(access_token, user.user_id, message_id, message.text)
    
    if response:
        await message.reply("Ваш ответ отправлен.")
    else:
        await message.reply("Не удалось отправить ответ.")