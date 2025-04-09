import logging
import aiohttp
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


access_token_cache = {}

async def get_access_token(client_id, client_secret):
    cache_key = (client_id, client_secret)
    cached = access_token_cache.get(cache_key)
    
    if cached and datetime.now() < cached['expires']:
        logger.info(f"Используем кэшированный токен: {cached['token'][:10]}...")
        return cached['token']

    url = "https://api.avito.ru/token/"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                logger.info(f"Статус запроса токена: {response.status}")
                response_data = await response.json()
                logger.info(f"Ответ Avito: {response_data}")

                if response.status != 200:
                    error_msg = response_data.get("error", "Неизвестная ошибка")
                    raise Exception(f"Ошибка API: {error_msg}")

                access_token = response_data.get('access_token')
                expires_in = response_data.get('expires_in', 3600)
                
                if access_token:
                    access_token_cache[cache_key] = {
                        'token': access_token,
                        'expires': datetime.now() + timedelta(seconds=expires_in)
                    }
                    logger.info(f"Новый токен получен: {access_token[:10]}...")
                    return access_token
                
                logger.error("Access token не найден в ответе")
                return None
    except Exception as e:
        logger.error(f"Ошибка запроса токена: {str(e)}")
        return None


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
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "message": {
            "text": message_text
        },
        "type": "text"
    }
    
    logger.info(f"Отправка сообщения в Avito: {message_text[:50]}...")  # Логируем начало
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                response_body = await response.text()
                logger.debug(f"Ответ Avito: {response.status} {response_body}")
                
                # Исправленная проверка статуса
                if response.status != 200:
                    logger.error(f"Ошибка API: {response.status}")
                    return None
                
                return await response.json()
                
        except Exception as e:
            logger.error(f"Ошибка отправки: {str(e)}")
            return None


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
            