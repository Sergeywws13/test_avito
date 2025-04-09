import asyncio
from aiogram import Bot
from sqlalchemy import select
from src.models.message_link import MessageLink
from src.models.user import User
from src.services.avito_api import get_access_token, get_chats, get_messages_from_chat, get_self_info, get_user_info, mark_chat_as_read, send_message
from src.database.db import async_session
from datetime import datetime
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_and_send_messages(bot: Bot, access_token: str, avito_user_id: str, telegram_chat_id: int):
    logger.info(f"Начинаем обработку сообщений для Avito ID: {avito_user_id}")
    
    try:
        self_info = await get_self_info(access_token)
        if not self_info or "id" not in self_info:
            logger.error("Не удалось получить информацию о пользователе Avito, возможно, токен недействителен")
            return

        chats_response = await get_chats(access_token, avito_user_id, unread_only=True)
        if not chats_response or "chats" not in chats_response:
            logger.info("Нет новых чатов с сообщениями или ошибка запроса")
            return

        for chat in chats_response["chats"]:
            chat_id = chat["id"]
            messages_response = await get_messages_from_chat(access_token, avito_user_id, chat_id)
            if not messages_response or "messages" not in messages_response:
                continue

            last_unread_message = next(
                (msg for msg in reversed(messages_response["messages"]) if not msg["isRead"]),
                None
            )
            if not last_unread_message:
                continue

            logger.debug(f"Последнее непрочитанное сообщение: {last_unread_message}")
            logger.debug(f"Пользователи чата: {chat['users']}")

            # Определяем отправителя
            if "author" in last_unread_message and "id" in last_unread_message["author"]:
                sender_id = last_unread_message["author"]["id"]
            else:
                # Если 'author' отсутствует, определяем отправителя из chat["users"]
                sender_id = next(
                    (user["id"] for user in chat["users"] if user["id"] != avito_user_id),
                    avito_user_id  # Если собеседник не найден, считаем системным или своим
                )

            sender_name = next(
                (user["name"] for user in chat["users"] if user["id"] == sender_id),
                "Неизвестный отправитель" if sender_id != avito_user_id else "Вы"
            )

            message_id = last_unread_message["id"]
            message_text = last_unread_message["content"]["text"]
            created_time = datetime.fromtimestamp(last_unread_message["created"])

            formatted_message = (
                f"📨 *Новое сообщение от {sender_name}*\n\n"
                f"💬 Текст: _{message_text}_\n\n"
                f"🕒 Время: {created_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"🔗 ID чата: `{chat_id}`"
            )

            sent_message = await bot.send_message(
                chat_id=telegram_chat_id,
                text=formatted_message,
                parse_mode="Markdown"
            )

            async with async_session() as session:
                user = await session.execute(
                    select(User).where(User.telegram_chat_id == telegram_chat_id)
                )
                user = user.scalar_one_or_none()
                if user:
                    new_link = MessageLink(
                        telegram_message_id=sent_message.message_id,
                        avito_chat_id=chat_id,
                        avito_user_id=sender_id,
                        user_id=user.id,
                        avito_message_id=message_id
                    )
                    session.add(new_link)
                    await session.commit()

            await mark_chat_as_read(access_token, avito_user_id, chat_id)

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise


async def send_message_to_avito(telegram_message_id, reply_text):
    async with async_session() as session:
        # Step 1: Fetch the MessageLink using telegram_message_id
        message_link = await session.execute(
            select(MessageLink).where(MessageLink.telegram_message_id == telegram_message_id)
        )
        message_link = message_link.scalar_one_or_none()

        if not message_link:
            logger.error(f"Связь с сообщением {telegram_message_id} не найдена в базе данных")
            return None

        # Step 2: Fetch the bot's user using message_link.user_id
        user = await session.get(User, message_link.user_id)
        if not user:
            logger.error(f"Пользователь с ID {message_link.user_id} не найден")
            return None

        # Step 3: Get the access token and send the message
        access_token = await get_access_token(user.client_id, user.client_secret)
        if not access_token:
            logger.error("Не удалось получить access token")
            return None

        logger.debug(f"Отправка сообщения в чат {message_link.avito_chat_id} от Avito ID {user.avito_user_id}")
        response = await send_message(
            access_token=access_token,
            avito_user_id=user.avito_user_id,  # Bot's Avito ID
            avito_chat_id=message_link.avito_chat_id,
            message_text=reply_text
        )

        if response and "message_id" in response:
            logger.info("Ответ успешно отправлен в Avito")
            return response
        else:
            logger.error(f"Не удалось отправить сообщение в Avito, ответ: {response}")
            return None


async def periodic_message_check(bot: Bot):
    while True:
        async with async_session() as session:
            users = await session.execute(select(User))
            users = users.scalars().all()

            for user in users:
                logger.info(f"Проверка сообщений для Telegram ID: {user.user_id}, Avito ID: {user.avito_user_id}")
                access_token = await get_access_token(user.client_id, user.client_secret)
                if access_token and user.telegram_chat_id and user.avito_user_id:
                    await fetch_and_send_messages(bot, access_token, user.avito_user_id, user.telegram_chat_id)
                else:
                    logger.warning(f"Пропущен пользователь: Telegram ID {user.user_id}, нет avito_user_id или telegram_chat_id")
        await asyncio.sleep(5)  # Увеличили интервал для тестов