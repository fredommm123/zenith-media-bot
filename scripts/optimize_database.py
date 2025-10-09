"""
Скрипт оптимизации базы данных
Добавляет индексы для ускорения запросов и оптимизирует структуру БД
"""
import asyncio
import aiosqlite
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = "bot_database.db"


async def create_backup():
    """Создание резервной копии перед оптимизацией"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"bot_database_backup_before_optimization_{timestamp}.db"
    
    try:
        shutil.copy2(DATABASE_PATH, backup_name)
        logger.info(f"✅ Бэкап создан: {backup_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return False


async def add_indexes(db: aiosqlite.Connection):
    """Добавление индексов для оптимизации запросов"""
    
    indexes = [
        # Индексы для таблицы users
        ("idx_users_balance", "CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance)"),
        ("idx_users_tier", "CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)"),
        ("idx_users_referrer", "CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id)"),
        ("idx_users_created", "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)"),
        
        # Индексы для таблицы videos
        ("idx_videos_user", "CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)"),
        ("idx_videos_status", "CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)"),
        ("idx_videos_platform", "CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)"),
        ("idx_videos_created", "CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)"),
        ("idx_videos_user_status", "CREATE INDEX IF NOT EXISTS idx_videos_user_status ON videos(user_id, status)"),
        ("idx_videos_platform_status", "CREATE INDEX IF NOT EXISTS idx_videos_platform_status ON videos(platform, status)"),
        
        # Индексы для таблицы youtube_channels
        ("idx_yt_channels_user", "CREATE INDEX IF NOT EXISTS idx_yt_channels_user_id ON youtube_channels(user_id)"),
        ("idx_yt_channels_channel", "CREATE INDEX IF NOT EXISTS idx_yt_channels_channel_id ON youtube_channels(channel_id)"),
        
        # Индексы для таблицы crypto_payouts
        ("idx_crypto_payouts_user", "CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user_id ON crypto_payouts(user_id)"),
        ("idx_crypto_payouts_status", "CREATE INDEX IF NOT EXISTS idx_crypto_payouts_status ON crypto_payouts(status)"),
        ("idx_crypto_payouts_video", "CREATE INDEX IF NOT EXISTS idx_crypto_payouts_video_id ON crypto_payouts(video_id)"),
        ("idx_crypto_payouts_created", "CREATE INDEX IF NOT EXISTS idx_crypto_payouts_created_at ON crypto_payouts(created_at)"),
        ("idx_crypto_payouts_user_status", "CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user_status ON crypto_payouts(user_id, status)"),
        
        # Индексы для таблицы tiktok_accounts
        ("idx_tiktok_accounts_user", "CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_user_id ON tiktok_accounts(user_id)"),
        ("idx_tiktok_accounts_username", "CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_username ON tiktok_accounts(username)"),
        
        # Индексы для таблицы referrals
        ("idx_referrals_referrer", "CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id)"),
        ("idx_referrals_referred", "CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id)"),
    ]
    
    logger.info("📊 Добавление индексов...")
    
    for index_name, query in indexes:
        try:
            await db.execute(query)
            logger.info(f"  ✅ {index_name}")
        except Exception as e:
            logger.warning(f"  ⚠️ {index_name}: {e}")
    
    await db.commit()
    logger.info("✅ Индексы добавлены")


async def optimize_database_settings(db: aiosqlite.Connection):
    """Оптимизация настроек SQLite"""
    
    settings = [
        # WAL режим для лучшей конкурентности
        ("PRAGMA journal_mode=WAL", "WAL mode"),
        
        # Увеличиваем таймаут блокировки
        ("PRAGMA busy_timeout=30000", "Busy timeout"),
        
        # Кэш страниц в памяти (10MB)
        ("PRAGMA cache_size=-10000", "Cache size"),
        
        # Синхронизация (NORMAL - баланс между скоростью и безопасностью)
        ("PRAGMA synchronous=NORMAL", "Synchronous mode"),
        
        # Автоматическая очистка временных файлов
        ("PRAGMA temp_store=MEMORY", "Temp store"),
        
        # Оптимизация памяти
        ("PRAGMA mmap_size=268435456", "Memory-mapped I/O (256MB)"),
    ]
    
    logger.info("⚙️ Оптимизация настроек БД...")
    
    for query, description in settings:
        try:
            await db.execute(query)
            logger.info(f"  ✅ {description}")
        except Exception as e:
            logger.warning(f"  ⚠️ {description}: {e}")
    
    await db.commit()
    logger.info("✅ Настройки оптимизированы")


async def analyze_database(db: aiosqlite.Connection):
    """Анализ и оптимизация таблиц"""
    
    logger.info("🔍 Анализ базы данных...")
    
    try:
        # ANALYZE собирает статистику для оптимизатора запросов
        await db.execute("ANALYZE")
        logger.info("  ✅ Статистика собрана")
        
        # VACUUM очищает базу данных и дефрагментирует
        logger.info("  🧹 Очистка и дефрагментация (может занять время)...")
        await db.execute("VACUUM")
        logger.info("  ✅ База данных оптимизирована")
        
    except Exception as e:
        logger.error(f"  ❌ Ошибка анализа: {e}")


async def get_database_stats(db: aiosqlite.Connection):
    """Получение статистики базы данных"""
    
    logger.info("📊 Статистика базы данных:")
    
    tables = ['users', 'videos', 'youtube_channels', 'crypto_payouts', 'tiktok_accounts']
    
    for table in tables:
        try:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
            count = await cursor.fetchone()
            logger.info(f"  • {table}: {count[0]} записей")
        except Exception as e:
            logger.warning(f"  ⚠️ {table}: {e}")
    
    # Размер базы данных
    try:
        cursor = await db.execute("PRAGMA page_count")
        page_count = (await cursor.fetchone())[0]
        
        cursor = await db.execute("PRAGMA page_size")
        page_size = (await cursor.fetchone())[0]
        
        size_mb = (page_count * page_size) / (1024 * 1024)
        logger.info(f"  • Размер БД: {size_mb:.2f} MB")
    except Exception as e:
        logger.warning(f"  ⚠️ Не удалось получить размер: {e}")


async def check_indexes(db: aiosqlite.Connection):
    """Проверка существующих индексов"""
    
    logger.info("🔍 Существующие индексы:")
    
    try:
        cursor = await db.execute(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        indexes = await cursor.fetchall()
        
        if indexes:
            for index_name, table_name in indexes:
                logger.info(f"  • {index_name} на таблице {table_name}")
        else:
            logger.info("  ⚠️ Индексы не найдены")
            
    except Exception as e:
        logger.error(f"  ❌ Ошибка проверки индексов: {e}")


async def main():
    """Главная функция оптимизации"""
    
    logger.info("🚀 Начало оптимизации базы данных")
    logger.info(f"📁 База данных: {DATABASE_PATH}")
    
    # Создание бэкапа
    if not await create_backup():
        logger.error("❌ Не удалось создать бэкап. Прерывание оптимизации.")
        return
    
    try:
        async with aiosqlite.connect(DATABASE_PATH, timeout=60.0) as db:
            # Получение текущей статистики
            await get_database_stats(db)
            
            # Проверка существующих индексов
            await check_indexes(db)
            
            # Добавление индексов
            await add_indexes(db)
            
            # Оптимизация настроек
            await optimize_database_settings(db)
            
            # Анализ и очистка
            await analyze_database(db)
            
            # Финальная статистика
            logger.info("\n📊 Финальная статистика:")
            await get_database_stats(db)
            
        logger.info("\n✅ Оптимизация завершена успешно!")
        logger.info("💡 Рекомендуется перезапустить бота для применения изменений")
        
    except Exception as e:
        logger.error(f"\n❌ Ошибка оптимизации: {e}")
        logger.error("💡 Восстановите базу данных из бэкапа при необходимости")


if __name__ == "__main__":
    asyncio.run(main())
