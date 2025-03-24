from aiogram import types, Router
from src.services.message_service import send_message_to_avito


check_router = Router()

@check_router.callback_query()
async def handle_reply(callback_query):
    """
    Обработчик для ответа на сообщение.
    """
    data = callback_query.data
    if data.startswith("reply_"):
        message_id = data.split("_")[1]
        await callback_query.answer("Введите ваш ответ:")
        
        # Сохраняем состояние, чтобы ожидать ответ
        await callback_query.message.answer("Введите ваш ответ:")
        await callback_query.message.bot.set_state("waiting_for_reply", message_id)

@check_router.message()
async def handle_incoming_reply(message: types.Message):
    """
    Обработчик для входящих ответов на сообщения.
    """
    state = message.bot.get_state()
    if state == "waiting_for_reply":
        message_id = state.get("message_id")
        
        # Здесь вы можете отправить ответ через API Avito
        await send_message_to_avito(message_id, message.text)

        await message.reply("Ваш ответ отправлен.")
        await message.bot.clear_state()
            