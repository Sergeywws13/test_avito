from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def generate_reply_markup(message_id):
    """
    Генерирует кнопки для ответа на сообщение.
    """
    keyboard = InlineKeyboardMarkup()
    reply_button = InlineKeyboardButton("Ответить", callback_data=f"reply_{message_id}")
    keyboard.add(reply_button)
    return keyboard
