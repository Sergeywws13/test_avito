from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def generate_reply_markup(message_id):
    """
    Генерирует кнопки для ответа на сообщение.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message_id}")]
    ])
    return keyboard