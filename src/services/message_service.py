import asyncio
from aiogram import Bot
from sqlalchemy import select
from src.models.user import User
from src.services.avito_api import get_access_token, get_chats, get_messages_from_chat, get_self_info, send_reply_to_message
from src.database.db import async_session
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
    chats = await get_chats(access_token, user_id)
    logger.info(f"Полученные чаты: {chats}")
    
    for chat in chats["chats"]:
        chat_id = chat["id"]  # ID чата из API Avito
        messages = await get_messages_from_chat(access_token, user_id, chat_id)
        logger.info(f"Полученные сообщения из чата {chat_id}: {messages}")
        
        for message in messages["messages"]:
            logger.info(f"Обработка сообщения: {message}")
            
            # Форматируем сообщение для отправки в Telegram
            message_text = message["content"]["text"]
            sender_id = message["author_id"]  # ID отправителя
            message_id = message["id"]  # ID сообщения
            created_time = message["created"]  # Время создания сообщения
            
            # Форматируем сообщение с дополнительной информацией
            formatted_message = (
                f"**Новое сообщение от пользователя {sender_id}:**\n\n"
                f"**Текст:** {message_text}\n"
                f"**ID сообщения:** {message_id}\n"
                f"**Время создания:** {created_time}\n\n"
                "Ответьте на это сообщение, чтобы ответить пользователю."
            )
            
            # Отправляем сообщение в Telegram
            try:
                await bot.send_message(telegram_chat_id, formatted_message)
                logger.info(f"Сообщение отправлено в чат {telegram_chat_id}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в чат {telegram_chat_id}: {e}")
            
            # Добавляем задержку между отправкой сообщений
            await asyncio.sleep(1)  # Задержка в 1 секунду


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
                response = await send_reply_to_message(access_token, user.user_id, chat_id, reply_text)

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
        await asyncio.sleep(60)