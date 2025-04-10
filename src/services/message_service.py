import asyncio
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.message_link import MessageLink
from src.models.user import User
from src.services.avito_api import get_access_token, get_chats, get_messages_from_chat, get_self_info, mark_chat_as_read, send_message
from src.database.db import async_session
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
                f"👉 Перейдите [по ссылке]({chat['users'][0]['public_user_profile']['url']}) к профилю отправителя"  # Новый формат ссылки
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


async def send_message_to_avito(telegram_message_id: int, reply_text: str):
    """Единственная функция для отправки сообщений в Avito"""
    async with async_session() as session:
        try:
            # Шаг 1: Получаем связь сообщения
            message_link = await session.execute(
                select(MessageLink).where(
                    MessageLink.telegram_message_id == telegram_message_id
                )
            )
            message_link = message_link.scalar_one_or_none()

            if not message_link:
                logger.error(f"MessageLink не найден для ID: {telegram_message_id}")
                return None

            # Шаг 2: Получаем пользователя
            user = await session.get(User, message_link.user_id)
            if not user:
                logger.error(f"Пользователь не найден: ID {message_link.user_id}")
                return None

            # Шаг 3: Получаем токен
            access_token = await get_access_token(user.client_id, user.client_secret)
            if not access_token:
                logger.error("Ошибка получения access_token")
                return None

            # Шаг 4: Отправляем сообщение
            logger.debug(
                f"Отправка в чат {message_link.avito_chat_id}, "
                f"Avito ID: {user.avito_user_id}, "
                f"Текст: {reply_text}"
            )

            response = await send_message(
                access_token=access_token,
                avito_user_id=user.avito_user_id,
                avito_chat_id=message_link.avito_chat_id,
                message_text=reply_text
            )

            # Исправленная проверка ответа
            if response and isinstance(response, dict) and response.get("id"):
                # Проверка на существующую запись
                existing = await session.execute(
                    select(MessageLink).where(
                        MessageLink.telegram_message_id == telegram_message_id
                    )
                )
                if existing.scalar():
                    logger.warning(f"MessageLink {telegram_message_id} уже существует")
                    return response
                
                new_link = MessageLink(
                    telegram_message_id=telegram_message_id,
                    avito_chat_id=message_link.avito_chat_id,
                    avito_user_id=str(user.avito_user_id),  # Приведение к строке
                    user_id=user.id,
                    avito_message_id=response["id"]
                )
                session.add(new_link)
                
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    logger.warning("Обнаружен дубликат, откат транзакции")
                    return response

                logger.info(f"Успешно сохранено: {response['id']}")
                return response
            
            logger.error(f"Некорректный ответ: {response}")
            return None

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
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
        await asyncio.sleep(1)  # Увеличили интервал для тестов



async def delete_old_messages(session: AsyncSession):
    # Установка ограничения на количество сообщений
    limit = 10000
    
    # Получение старых сообщений
    old_messages = await session.execute(
        select(MessageLink).order_by(MessageLink.id.asc()).limit(limit)
    )
    
    # Удаление старых сообщений
    for message in old_messages.scalars().all():
        await session.delete(message)
        print(f"Удалено сообщение с ID {message.id}")
    
    # Сохранение изменений
    await session.commit()

    # Проверка содержимого базы данных после удаления сообщений
    messages_after_deletion = await session.execute(
        select(MessageLink).order_by(MessageLink.id.asc())
    )
    
    # Проверка, что записи, которые должны быть удалены, действительно отсутствуют в таблице
    if messages_after_deletion.scalars().all():
        print("Сообщения не были удалены")
    else:
        print("Сообщения были удалены успешно")


async def delete_old_messages_daily():
    async with async_session() as session:
        await delete_old_messages(session)
        print(f"Удалены старые сообщения {datetime.now()}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(delete_old_messages_daily, 'cron', day='*/3', hour=0, minute=0, second=0)
    scheduler.start()
