import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable

import config
from database import Database
from handlers import profile, videos, payments, referral, help, admin, tiktok, youtube, youtube_videos, payouts, admin_settings
from crypto_pay import test_crypto_connection, close_crypto_session

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def user_registration_middleware(
    handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
    event: Update,
    data: Dict[str, Any]
) -> Any:
    """Middleware для проверки пользователей (без автоматической регистрации)"""
    # Регистрация происходит только через /start для сохранения реферальной ссылки
    return await handler(event, data)


async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    db = Database(config.DATABASE_PATH)
    await db.init_db()
    logger.info("Database initialized")
    
    # Проверка подключения к Crypto Pay API
    crypto_ok = await test_crypto_connection()
    if not crypto_ok:
        logger.warning("⚠️ Crypto Pay API недоступен. Выплаты могут не работать!")
    
    # Регистрация middleware
    dp.update.outer_middleware(user_registration_middleware)
    
    # Регистрация роутеров
    dp.include_router(profile.router)
    dp.include_router(videos.router)
    dp.include_router(payments.router)
    dp.include_router(referral.router)
    dp.include_router(help.router)
    dp.include_router(admin.router)
    dp.include_router(admin_settings.router)
    dp.include_router(tiktok.router)
    dp.include_router(youtube.router)
    dp.include_router(youtube_videos.router)
    dp.include_router(payouts.router)
    
    logger.info("Bot started")
    
    # Запуск бота
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_crypto_session()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
