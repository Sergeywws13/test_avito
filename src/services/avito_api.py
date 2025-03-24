import json
import logging
import aiohttp
from datetime import date, timedelta

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


async def get_chats(access_token, user_id):
    logger.info(f"Запрос на получение списка чатов: user_id={user_id}")
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                logger.info(f"Ответ на запрос: {response.status}")
                response.raise_for_status()
                data = await response.json()
                logger.info(f"Данные: {data}")
                return data.get("chats", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка чатов: {e}")
            return []


async def get_messages(access_token, user_id, chat_id):
    """
    Получает сообщения из чата через API Авито.
    """
    url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                # Ожидаем результат вызова json()
                data = await response.json()
                return data.get("messages", [])
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений: {e}")
            return []


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
        

async def send_message(access_token, user_id, chat_id, message_text):
    """
    Отправляет сообщение через API Авито.
    """
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
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
        