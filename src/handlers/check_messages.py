from aiogram import types, Router
from aiogram.fsm.context import FSMContext

from src.services.avito_api import send_reply_to_message


check_router = Router()


@check_router.message()
async def handle_incoming_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    access_token = data.get("access_token")
    user_id = data.get("user_id")
    message_id = data.get("message_id")

    if not access_token or not user_id or not message_id:
        await message.reply("Не удалось получить данные для отправки ответа.")
        return

    # Отправляем ответ на сообщение через API Avito
    await send_reply_to_message(access_token, user_id, message_id, message.text)
    
    await message.reply("Ваш ответ отправлен.")
    await state.clear()  # Очистка состояния после отправки ответа
