import logging
from aiogram import types, Router
from sqlalchemy import select
from src.models.message_link import MessageLink
from src.services.message_service import send_message_to_avito
from src.database.db import async_session
from src.models.user import User

# Инициализация роутера
check_router = Router()

# Обработчик для получения входящих сообщений
@check_router.message()
async def handle_incoming_message(message: types.Message):
    # Проверяем, является ли сообщение ответом на другое сообщение
    if message.reply_to_message:
        await handle_incoming_reply(message)
    else:
        await message.answer("Пожалуйста, ответьте на это сообщение.")

async def handle_incoming_reply(message: types.Message):
    if not message.reply_to_message:
        await message.reply("❌ Это сообщение не является ответом")
        return

    reply_to_message_id = message.reply_to_message.message_id
    reply_text = message.text

    try:
        # Отправляем сообщение в Avito и получаем ответ
        response = await send_message_to_avito(reply_to_message_id, reply_text)
        logging.info(f"Ответ от Avito: {response}")

        # Проверяем, что ответ не пустой и содержит ожидаемые данные
        if response and isinstance(response, dict) and "message_id" in response:
            await save_message_link(reply_to_message_id, message.message_id, response['message_id'])
            await message.reply("✅ Ответ успешно отправлен в Avito")
        else:
            logging.error(f"Ошибка в ответе от Avito: {response}")
            await message.reply("❌ Ошибка отправки: не удалось отправить сообщение в Avito. Проверьте логи.")
    except Exception as e:
        await message.reply(f"⛔ Критическая ошибка: {str(e)}")
        logging.error(f"Ошибка отправки: {str(e)}")

async def save_message_link(reply_to_message_id, telegram_message_id, avito_message_id):
    async with async_session() as session:
        # Получаем связь с сообщением
        message_link = await session.execute(
            select(MessageLink).where(MessageLink.telegram_message_id == reply_to_message_id)
        )
        message_link = message_link.scalar_one_or_none()

        if message_link:
            user = await session.get(User, message_link.user_id)
            if user:
                new_link = MessageLink(
                    telegram_message_id=telegram_message_id,
                    avito_chat_id=message_link.avito_chat_id,
                    avito_user_id=user.avito_user_id,
                    user_id=user.id,
                    avito_message_id=avito_message_id
                )
                session.add(new_link)
                await session.commit()
            else:
                logging.error(f"Пользователь с ID {message_link.user_id} не найден.")
        else:
            logging.error(f"Связь с сообщением {reply_to_message_id} не найдена в базе данных.")