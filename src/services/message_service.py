import asyncio
from aiogram import Bot
from sqlalchemy import select
from src.models.user import User
from src.services.avito_api import get_access_token, get_chats, get_messages_from_chat, get_self_info, get_user_info, mark_chat_as_read, send_message
from src.database.db import async_session
from datetime import datetime
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_and_send_messages(bot: Bot, access_token, user_id, telegram_chat_id):
    logger.info("Начинаем обработку сообщений...")
    
    # Получаем информацию о текущем пользователе
    self_info = await get_self_info(access_token)
    user_id = self_info["id"]
    
    # Получаем список чатов
    chats = await get_chats(access_token, user_id, unread_only=True)
    logger.info(f"Полученные чаты: {chats}")
    
    for chat in chats["chats"]:
        chat_id = chat["id"]  # ID чата из API Avito
        messages = await get_messages_from_chat(access_token, user_id, chat_id)
        logger.info(f"Полученные сообщения из чата {chat_id}: {messages}")
        
        if messages["messages"]:  # Проверяем, есть ли непрочитанные сообщения
            last_message = next((message for message in reversed(messages["messages"]) if not message["isRead"]), None)
            if last_message:
                logger.info(f"Обработка сообщения: {last_message}")
                
                # Получаем информацию о пользователе
                sender_id = last_message["author_id"]
                sender_name = next((user["name"] for user in chat["users"] if user["id"] == sender_id), "Неизвестный пользователь")
                
                # Форматируем сообщение для отправки в Telegram
                message_text = last_message["content"]["text"]
                message_id = last_message["id"]  # ID сообщения
                created_time = last_message["created"]  # Время создания сообщения
                
                # Форматируем сообщение с дополнительной информацией
                formatted_message = (
                    f"📨 Новое сообщение от {sender_name} 📨\n\n"
                    f"📝 Текст сообщения: {message_text}\n\n"
                    f"📊 ID сообщения: {message_id}\n\n"
                    f"🕰️ Время создания: {datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                
                # Отправляем сообщение в Telegram
                try:
                    await bot.send_message(telegram_chat_id, formatted_message)
                    logger.info(f"Сообщение отправлено в чат {telegram_chat_id}.")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения в чат {telegram_chat_id}: {e}")
                
                # Помечаем сообщение как прочитанное
                await mark_chat_as_read(access_token, user_id, chat_id)
                break


async def send_message_to_avito(message_id, reply_text):
    """
    Отправляет ответ на сообщение через API Avito.
    """
    # Получаем информацию о сообщении, на которое мы отвечаем
    async with async_session() as session:
        # Здесь вам нужно будет получить пользователя, чтобы использовать его client_id и client_secret
        user = await session.execute(select(User).where(User.user_id == message_id))
        user = user.scalar_one_or_none()

        if user:
            # Получаем access_token для отправки сообщения
            access_token = await get_access_token(user.client_id, user.client_secret)
            if access_token:
                # Здесь вам нужно будет использовать API Avito для отправки ответа
                # Используем функцию send_message, передавая необходимые параметры
                chat_id = message_id  # ID чата, на который мы отвечаем
                response = await send_message(access_token, user.user_id, chat_id, reply_text)

                if response:
                    logger.info("Ответ успешно отправлен в Avito.")
                else:
                    logger.error("Не удалось отправить ответ в Avito.")
            else:
                logger.error("Не удалось получить access token.")
        else:
            logger.error("Пользователь не найден в базе данных.")


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
                access_token = await get_access_token(user.client_id, user.client_secret)
                if access_token and user.telegram_chat_id:
                    await fetch_and_send_messages(bot, access_token, user.user_id, user.telegram_chat_id)
        await asyncio.sleep(1)