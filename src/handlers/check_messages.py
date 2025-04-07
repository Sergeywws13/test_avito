import logging
from aiogram import types, Router
from sqlalchemy import select
from src.models.message_link import MessageLink
from src.services.avito_api import get_access_token, get_chats, get_self_info, send_message, send_message_to_avito
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
    if not message.reply_to_message:
        await message.reply("❌ Это сообщение не является ответом")
        return

    reply_to_message_id = message.reply_to_message.message_id
    reply_text = message.text

    try:
        response = await send_message_to_avito(reply_to_message_id, reply_text)
        if response and 'message_id' in response:
            # Сохраняем информацию о новом сообщении в базе данных
            async with async_session() as session:
                message_link = await session.execute(
                    select(MessageLink).where(MessageLink.telegram_message_id == reply_to_message_id)
                )
                message_link = message_link.scalar_one_or_none()

                if message_link:
                    user = await session.get(User, message_link.user_id)
                    new_link = MessageLink(
                        telegram_message_id=message.message_id,
                        avito_chat_id=message_link.avito_chat_id,
                        avito_user_id=user.avito_user_id,  # Сохраняем ваш avito_user_id
                        user_id=user.id,
                        avito_message_id=response['message_id']
                    )
                    session.add(new_link)
                    await session.commit()

            await message.reply("✅ Ответ успешно отправлен в Avito")
        else:
            await message.reply("❌ Ошибка отправки: не удалось отправить сообщение в Avito. Проверьте логи.")

    except Exception as e:
        await message.reply(f"⛔ Критическая ошибка: {str(e)}")
        logging.error(f"Error in message reply: {str(e)}")