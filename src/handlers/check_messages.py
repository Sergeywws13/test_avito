from aiogram import types, Router
from aiogram.fsm.context import FSMContext

from src.services.avito_api import send_reply_to_message


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
async def handle_incoming_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    access_token = data.get("access_token")
    user_id = data.get("user_id")

    if not access_token or not user_id:
        await message.reply("Не удалось получить данные для отправки ответа.")
        return

    chat_id = message.reply_to_message.chat.id  # ID чата, в котором было сообщение
    
    # Отправляем ответ на сообщение через API Avito
    await send_reply_to_message(access_token, user_id, chat_id, message.text)
    
    await message.reply("Ваш ответ отправлен.")
            
