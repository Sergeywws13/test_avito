import json
import logging
import requests
import time
from datetime import date, timedelta

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_access_token(client_id, client_secret):
    """
    Получает access_token от API Avito.

    :param client_id: Идентификатор клиента (Client ID)
    :param client_secret: Секретный ключ клиента (Client Secret)
    :return: Access token или False в случае ошибки
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
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        if data.get("access_token"):
            print(data['access_token'])
            return data['access_token']
        else:
            logger.error("Access token не найден в ответе")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе access_token: {e}")
        return False


def get_self_info(access_token):
    """
    Получает информацию о текущем аккаунте через API Avito.

    :param access_token: Access token для авторизации
    :return: JSON с информацией о аккаунте или код статуса HTTP в случае ошибки
    """
    url = "https://api.avito.ru/core/v1/accounts/self"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе информации о аккаунте: {e}")
        return response.status_code


def get_chats(access_token, user_id):
    """
    Получает список чатов через API Avito.
    """
    url = f"https://api.avito.ru/messenger/v2/accounts/{user_id}/chats"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "unread_only": True,
        "chat_types": "u2i"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("chats", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении чатов: {e}")
        return []

def get_messages(access_token, user_id, chat_id, limit=100, offset=0):
    """
    Получает сообщения из чата через API Avito.
    """
    url = f"https://api.avito.ru/messenger/v3/accounts/{user_id}/chats/{chat_id}/messages/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "unread_only": True
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        return []

def mark_chat_as_read(access_token, user_id, chat_id):
    """
    Помечает чат как прочитанный через API Avito.
    """
    url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/read"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при пометке чата как прочитанного: {e}")
        return None

def get_unread_messages(access_token, user_id):
    chats = get_chats(access_token, user_id)
    messages = []
    for chat in chats:
        chat_id = chat["id"]
        chat_messages = get_messages(access_token, user_id, chat_id)
        messages.extend(chat_messages)
    return messages
    

def send_message(access_token, user_id, chat_id, message_text):
    """
    Отправляет сообщение через API Avito.
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
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return None