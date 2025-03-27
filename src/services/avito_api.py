import logging
import aiohttp

from sqlalchemy import select
from src.database.db import async_session

from src.models.user import User

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_access_token(client_id, client_secret):
    """
    Получает access_token от API Avito.
    """
    url = "https://api.avito.ru/token/"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("access_token"):
                    return data['access_token']
                else:
                    logger.error("Access token не найден в ответе")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при запросе access_token: {e}")
            return False


async def get_self_info(access_token):
    """
    Получает информацию о текущем аккаунте через API Авито.
    """
    url = "https://api.avito.ru/core/v1/accounts/self"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка при запросе информации о аккаунте: {e}")
            return None


async def get_chats(access_token, user_id, unread_only=False):
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "chat_types": "u2i,u2u"  # Включить чаты от пользователей и по объявлениям
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return await response.json()


async def get_messages_from_chat(access_token, user_id, chat_id):
    url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()


async def mark_chat_as_read(access_token, user_id, chat_id):
    """
    Помечает чат как прочитанный через API Авито.
    """
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/read"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка при пометке чата как прочитанного: {e}")
            return None
        

async def send_message(access_token, avito_user_id, avito_chat_id, message_text):
    url = f"https://api.avito.ru/messenger/v1/accounts/{avito_user_id}/chats/{avito_chat_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "message": {
            "text": message_text
        },
        "type": "text"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return None


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
                response = await send_message(access_token, user.user_id, chat_id, reply_text)

                if response:
                    logger.info("Ответ успешно отправлен в Avito.")
                else:
                    logger.error("Не удалось отправить ответ в Avito.")
            else:
                logger.error("Не удалось получить access token.")
        else:
            logger.error("Пользователь не найден в базе данных.")
        

async def get_user_info(access_token, user_id):
    url = f"https://api.avito.ru/core/v1/accounts/{user_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None