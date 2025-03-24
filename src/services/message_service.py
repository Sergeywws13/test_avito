import asyncio
from aiogram import Bot
from sqlalchemy import select
from src.models.user import User
from src.services.avito_api import get_access_token, get_chats, get_messages, get_self_info, mark_chat_as_read, send_message
from src.database.db import async_session


async def fetch_and_send_messages(bot: Bot, access_token, user_id):
    """
    Получает непрочитанные сообщения из всех непрочитанных чатов и отправляет их в Telegram.
    """
    self_info = get_self_info(access_token)
    user_id = self_info["id"]
    chats = get_chats(access_token, user_id)
    for chat in chats:
        chat_id = chat["id"]
        messages = get_messages(access_token, user_id, chat_id)
        for message in messages:
            sender_name = message["sender"]["name"]
            sender_contact = message["sender"].get("contact", "Нет контакта")
            message_text = message["last_message"]["text"]
            formatted_message = f"**От:** {sender_name}\n**Контакт:** {sender_contact}\n\n{message_text}"
            await bot.send_message(user_id, formatted_message)  # Отправляем сообщение в Telegram
            mark_chat_as_read(access_token, user_id, chat_id)  # Помечаем чат как прочитанный # Помечаем чат как прочитанный


async def handle_telegram_message(message, access_token, user_id):
    """
    Обрабатывает входящие сообщения из Telegram и отправляет их в API Авито.
    """
    chat_id = message.chat.id
    response = send_message(access_token, user_id, chat_id, message.text)
    if response:
        await message.reply("Ваше сообщение отправлено.")
    else:
        await message.reply("Произошла ошибка при отправке сообщения.")


async def periodic_message_check(bot: Bot):
    """
    Периодически проверяет новые сообщения и отправляет их в Telegram.
    """
    while True:
        async with async_session() as session:
            # Получаем всех пользователей
            users = await session.execute(select(User))
            users = users.scalars().all()

            for user in users:
                access_token = get_access_token(user.client_id, user.client_secret)
                if access_token:
                    self_info = get_self_info(access_token)
                    user_id = self_info["id"]
                    await fetch_and_send_messages(bot, access_token, user_id)
        await asyncio.sleep(60)  # Проверка каждые 60 секунд