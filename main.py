import asyncio
from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN
import logging
from src.services.message_service import periodic_message_check, start_scheduler
from src.database.db import engine
from src.handlers.register import register_router
from src.handlers.start import start_router
from src.handlers.check_messages import check_router
from src.models.base import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(bot=bot)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    dp.include_router(start_router)
    dp.include_router(register_router)
    dp.include_router(check_router)

    # Запускаем периодическую проверку сообщений
    asyncio.create_task(periodic_message_check(bot))

    start_scheduler()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    