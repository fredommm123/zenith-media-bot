import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Включаем WAL режим для лучшей конкурентности
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=30000")  # 30 секунд
            await db.commit()

            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    balance REAL DEFAULT 0,
                    total_videos INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_withdrawn REAL DEFAULT 0,
                    referrer_id INTEGER,
                    referral_earnings REAL DEFAULT 0,
                    tier TEXT DEFAULT 'bronze',
                    last_key_issued_at TIMESTAMP,
                    blocked_until TIMESTAMP,
                    free_key_claimed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id)
                )
            """)

            # Таблица каналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, channel_id)
                )
            """)

            # Таблица роликов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_id INTEGER,
                    youtube_channel_id INTEGER,
                    platform TEXT DEFAULT 'tiktok',
                    video_url TEXT NOT NULL UNIQUE,
                    video_id TEXT UNIQUE,
                    tiktok_video_id TEXT,
                    video_title TEXT,
                    video_author TEXT,
                    video_published_at TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    favorites INTEGER DEFAULT 0,
                    earnings REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (channel_id) REFERENCES channels(id),
                    FOREIGN KEY (youtube_channel_id) REFERENCES youtube_channels(id)
                )
            """)

            # Миграция: добавляем tiktok_video_id если его нет
            try:
                await db.execute("ALTER TABLE videos ADD COLUMN tiktok_video_id TEXT")
                await db.commit()
                logger.info("✅ Добавлена колонка tiktok_video_id")
            except Exception:
                pass

            # Таблица заявок на вывод
            await db.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_details TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица способов выплат
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    method_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица рефералов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    earnings REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id),
                    UNIQUE(referrer_id, referred_id)
                )
            """)

            # Таблица TikTok аккаунтов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tiktok_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    url TEXT NOT NULL,
                    verification_code TEXT,
                    is_verified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица YouTube каналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS youtube_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    channel_id TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    channel_handle TEXT,
                    channel_name TEXT,
                    url TEXT NOT NULL,
                    verification_code TEXT,
                    is_verified INTEGER DEFAULT 0,
                    rate_per_1000_views REAL DEFAULT 50.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица выплат через Crypto Pay
            await db.execute("""
                CREATE TABLE IF NOT EXISTS crypto_payouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_id INTEGER NOT NULL,
                    amount_rub REAL NOT NULL,
                    amount_usdt REAL NOT NULL,
                    spend_id TEXT NOT NULL UNIQUE,
                    transfer_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    admin_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Таблица ключей для медиапартнёров
            await db.execute("""
                CREATE TABLE IF NOT EXISTS media_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'available',
                    is_free_promo INTEGER DEFAULT 0,
                    assigned_to INTEGER,
                    uploaded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_at TIMESTAMP,
                    FOREIGN KEY (assigned_to) REFERENCES users(user_id),
                    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
                )
            """)

            # Индексы для оптимизации запросов
            logger.info("Creating database indexes...")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_blocked_until ON users(blocked_until)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_status ON videos(user_id, status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform_status ON videos(platform, status)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_yt_channels_user_id ON youtube_channels(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_yt_channels_channel_id ON youtube_channels(channel_id)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user ON crypto_payouts(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_video ON crypto_payouts(video_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_status ON crypto_payouts(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_created_at ON crypto_payouts(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user_status ON crypto_payouts(user_id, status)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_user_id ON tiktok_accounts(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_username ON tiktok_accounts(username)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id)")

            await db.execute("CREATE INDEX IF NOT EXISTS idx_media_keys_status ON media_keys(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_media_keys_assigned_to ON media_keys(assigned_to)")

            # Оптимизация настроек БД
            await db.execute("PRAGMA cache_size=-10000")  # 10MB кэш
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA temp_store=MEMORY")

            # Добавляем колонку для даты выдачи ключа (если ещё нет)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_key_issued_at TIMESTAMP")
                await db.commit()
                logger.info("✅ Добавлена колонка last_key_issued_at")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN blocked_until TIMESTAMP")
                await db.commit()
                logger.info("✅ Добавлена колонка blocked_until")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN free_key_claimed_at TIMESTAMP")
                await db.commit()
                logger.info("✅ Добавлена колонка free_key_claimed_at")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE media_keys ADD COLUMN is_free_promo INTEGER DEFAULT 0")
                await db.commit()
                logger.info("✅ Добавлена колонка is_free_promo в media_keys")
            except Exception:
                pass

            await db.commit()
            logger.info("Database initialized successfully with optimized indexes")

    # === MEDIA KEY METHODS ===
    async def add_media_keys(
        self,
        keys: List[str],
        uploaded_by: Optional[int] = None,
        *,
        is_free_promo: bool = False,
    ) -> int:
        """Добавить список ключей"""
        if not keys:
            return 0
        inserted = 0
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            for raw_key in keys:
                key_value = raw_key.strip()
                if not key_value:
                    continue
                try:
                    await db.execute(
                        "INSERT INTO media_keys (key_value, uploaded_by, is_free_promo) VALUES (?, ?, ?)",
                        (key_value, uploaded_by, 1 if is_free_promo else 0)
                    )
                    inserted += 1
                except aiosqlite.IntegrityError:
                    continue
            await db.commit()
        return inserted

    async def count_available_media_keys(self, *, free_only: bool = False) -> int:
        """Количество доступных ключей"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                """
                SELECT COUNT(*)
                FROM media_keys
                WHERE status = 'available' AND is_free_promo = ?
                """,
                (1 if free_only else 0,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_next_available_media_key(self, *, free_only: bool = False) -> Optional[Dict[str, Any]]:
        """Получить ближайший свободный ключ"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT *
                FROM media_keys
                WHERE status = 'available' AND is_free_promo = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (1 if free_only else 0,),
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def mark_media_key_assigned(self, key_id: int, user_id: int):
        """Отметить ключ как выданный"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE media_keys
                        SET status = 'assigned', assigned_to = ?, assigned_at = CURRENT_TIMESTAMP
                        WHERE id = ?""",
                (user_id, key_id)
            )
            await db.commit()

    async def mark_media_key_status(
        self,
        key_id: int,
        status: str,
        *,
        clear_assignment: bool = False,
    ):
        """Обновить статус ключа"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            if clear_assignment:
                await db.execute(
                    """
                    UPDATE media_keys
                    SET status = ?, assigned_to = NULL, assigned_at = NULL
                    WHERE id = ?
                    """,
                    (status, key_id),
                )
            else:
                await db.execute(
                    "UPDATE media_keys SET status = ? WHERE id = ?",
                    (status, key_id),
                )
            await db.commit()

    async def update_user_last_key_issued(self, user_id: int, issued_at: Optional[datetime] = None):
        """Сохранить время последней выдачи ключа"""
        issued_ts = (issued_at or datetime.utcnow()).isoformat()
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET last_key_issued_at = ? WHERE user_id = ?",
                (issued_ts, user_id)
            )
            await db.commit()

    async def update_free_key_claim(self, user_id: int, *, claimed_at: Optional[datetime] = None):
        ts = (claimed_at or datetime.utcnow()).isoformat()
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET free_key_claimed_at = ? WHERE user_id = ?",
                (ts, user_id)
            )
            await db.commit()

    async def clear_free_key_claim(self, user_id: int):
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET free_key_claimed_at = NULL WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def set_user_block(self, user_id: int, days: int):
        until = (datetime.utcnow() + timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET blocked_until = ?, tier = 'banned' WHERE user_id = ?",
                (until, user_id)
            )
            await db.commit()

    async def clear_user_block(self, user_id: int):
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET blocked_until = NULL, tier = 'bronze' WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def get_user_active_free_key(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM media_keys
                WHERE assigned_to = ? AND is_free_promo = 1
                ORDER BY assigned_at DESC
                LIMIT 1
                """,
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_users_free_key_progress(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.full_name,
                    u.free_key_claimed_at,
                    u.blocked_until,
                    mk.id AS key_id,
                    mk.key_value,
                    mk.status AS key_status,
                    mk.assigned_at,
                    SUM(CASE WHEN v.platform = 'tiktok'
                        AND v.status = 'approved'
                        AND v.created_at BETWEEN u.free_key_claimed_at AND datetime(u.free_key_claimed_at, '+24 hours')
                        THEN 1 ELSE 0 END) AS tiktok_videos,
                    SUM(CASE WHEN v.platform = 'youtube'
                        AND v.status = 'approved'
                        AND v.created_at BETWEEN u.free_key_claimed_at AND datetime(u.free_key_claimed_at, '+24 hours')
                        THEN 1 ELSE 0 END) AS youtube_videos
                FROM users u
                LEFT JOIN media_keys mk
                    ON mk.assigned_to = u.user_id AND mk.is_free_promo = 1
                LEFT JOIN videos v
                    ON v.user_id = u.user_id
                WHERE u.free_key_claimed_at IS NOT NULL
                GROUP BY u.user_id, mk.id
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_user_free_key_progress(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                """
                SELECT
                    u.user_id,
                    u.username,
                    u.full_name,
                    u.free_key_claimed_at,
                    u.blocked_until,
                    mk.id AS key_id,
                    mk.key_value,
                    mk.status AS key_status,
                    mk.assigned_at
                FROM users u
                LEFT JOIN media_keys mk
                    ON mk.assigned_to = u.user_id AND mk.is_free_promo = 1
                WHERE u.user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ) as cursor:
                info = await cursor.fetchone()

            if not info or not info["free_key_claimed_at"]:
                return None

            claimed_raw: str = info["free_key_claimed_at"]
            claimed_at = datetime.fromisoformat(claimed_raw.replace(" ", "T"))
            deadline = claimed_at + timedelta(hours=24)

            start_str = claimed_at.strftime("%Y-%m-%d %H:%M:%S")
            end_str = deadline.strftime("%Y-%m-%d %H:%M:%S")

            async with db.execute(
                """
                SELECT
                    SUM(CASE WHEN platform = 'tiktok' AND status = 'approved'
                        AND created_at BETWEEN ? AND ? THEN 1 ELSE 0 END) AS tiktok_videos,
                    SUM(CASE WHEN platform = 'youtube' AND status = 'approved'
                        AND created_at BETWEEN ? AND ? THEN 1 ELSE 0 END) AS youtube_videos
                FROM videos
                WHERE user_id = ?
                """,
                (start_str, end_str, start_str, end_str, user_id),
            ) as cursor:
                progress = await cursor.fetchone()

            result = dict(info)
            result["claimed_at"] = claimed_at.isoformat()
            result["deadline"] = deadline.isoformat()
            result["tiktok_videos"] = (progress["tiktok_videos"] or 0) if progress else 0
            result["youtube_videos"] = (progress["youtube_videos"] or 0) if progress else 0
            return result

    async def has_user_claimed_free_key(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                """
                SELECT COUNT(*)
                FROM media_keys
                WHERE assigned_to = ? AND is_free_promo = 1
                """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row and row[0] > 0)

    async def set_user_free_key_status(
        self,
        user_id: int,
        *,
        key_id: Optional[int],
        status: str,
        blocked_until: Optional[datetime] = None,
        clear_claim: bool = False,
    ):
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute("BEGIN"):
                if key_id:
                    if status == 'available':
                        await db.execute(
                            """
                            UPDATE media_keys
                            SET status = 'available', assigned_to = NULL, assigned_at = NULL
                            WHERE id = ?
                            """,
                            (key_id,),
                        )
                    else:
                        await db.execute(
                            "UPDATE media_keys SET status = ? WHERE id = ?",
                            (status, key_id),
                        )

                updates = []
                params: List[Any] = []
                if blocked_until is not None:
                    updates.append("blocked_until = ?")
                    params.append(
                        blocked_until.isoformat() if isinstance(blocked_until, datetime) else blocked_until
                    )
                if clear_claim:
                    updates.append("free_key_claimed_at = NULL")
                if status == 'available':
                    updates.append("tier = 'bronze'")
                params.append(user_id)

                if updates:
                    await db.execute(
                        f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
                        params,
                    )

            await db.commit()

    async def get_users_for_key_distribution(self, min_videos: int, days: int) -> List[Dict[str, Any]]:
        """Получить пользователей, выполнивших условие по видео за период"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT u.*, COUNT(v.id) AS videos_count
                FROM users u
                JOIN videos v ON v.user_id = u.user_id
                WHERE v.status = 'approved'
                  AND v.created_at >= datetime('now', ?)
                  AND (u.last_key_issued_at IS NULL OR u.last_key_issued_at <= datetime('now', ?))
                  AND (u.blocked_until IS NULL OR u.blocked_until < datetime('now'))
                GROUP BY u.user_id
                HAVING videos_count >= ?
                ORDER BY videos_count DESC, u.created_at ASC
            """
            arg = f"-{days} days"
            async with db.execute(query, (arg, arg, min_videos)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_recently_assigned_media_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Последние выданные ключи"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT mk.*, u.username AS assigned_username
                FROM media_keys mk
                LEFT JOIN users u ON mk.assigned_to = u.user_id
                WHERE mk.status = 'assigned'
                ORDER BY mk.assigned_at DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    balance REAL DEFAULT 0,
                    total_videos INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_withdrawn REAL DEFAULT 0,
                    referrer_id INTEGER,
                    referral_earnings REAL DEFAULT 0,
                    tier TEXT DEFAULT 'bronze',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id)
                )
            """)

            # Таблица каналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, channel_id)
                )
            """)

            # Таблица роликов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_id INTEGER,
                    youtube_channel_id INTEGER,
                    platform TEXT DEFAULT 'tiktok',
                    video_url TEXT NOT NULL UNIQUE,
                    video_id TEXT UNIQUE,
                    tiktok_video_id TEXT,
                    video_title TEXT,
                    video_author TEXT,
                    video_published_at TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    favorites INTEGER DEFAULT 0,
                    earnings REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (channel_id) REFERENCES channels(id),
                    FOREIGN KEY (youtube_channel_id) REFERENCES youtube_channels(id)
                )
            """)
            
            # Миграция: добавляем tiktok_video_id если его нет
            try:
                await db.execute("ALTER TABLE videos ADD COLUMN tiktok_video_id TEXT")
                await db.commit()
                logger.info("✅ Добавлена колонка tiktok_video_id")
            except Exception as e:
                # Колонка уже существует
                pass

            # Таблица заявок на вывод
            await db.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_details TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица способов выплат
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    method_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица рефералов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    earnings REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id),
                    UNIQUE(referrer_id, referred_id)
                )
            """)

            # Таблица TikTok аккаунтов (один аккаунт = один пользователь навсегда)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tiktok_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    url TEXT NOT NULL,
                    verification_code TEXT,
                    is_verified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Индексы для быстрого поиска
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_tiktok_username ON tiktok_accounts(username)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_tiktok_user ON tiktok_accounts(user_id)"
            )

            # Таблица YouTube каналов (один канал = один пользователь навсегда)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS youtube_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    channel_id TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    channel_handle TEXT,
                    channel_name TEXT,
                    url TEXT NOT NULL,
                    verification_code TEXT,
                    is_verified INTEGER DEFAULT 0,
                    rate_per_1000_views REAL DEFAULT 50.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Индексы для YouTube
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_youtube_channel_id ON youtube_channels(channel_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_youtube_user ON youtube_channels(user_id)"
            )

            # Таблица выплат через Crypto Pay
            await db.execute("""
                CREATE TABLE IF NOT EXISTS crypto_payouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    video_id INTEGER NOT NULL,
                    amount_rub REAL NOT NULL,
                    amount_usdt REAL NOT NULL,
                    spend_id TEXT NOT NULL UNIQUE,
                    transfer_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    admin_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Таблица ключей для медиапартнёров
            await db.execute("""
                CREATE TABLE IF NOT EXISTS media_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'available',
                    assigned_to INTEGER,
                    uploaded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_at TIMESTAMP,
                    FOREIGN KEY (assigned_to) REFERENCES users(user_id),
                    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
                )
            """)

            # Индексы для оптимизации запросов
            logger.info("Creating database indexes...")
            
            # Индексы для users
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
            
            # Индексы для videos
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_status ON videos(user_id, status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform_status ON videos(platform, status)")
            
            # Индексы для youtube_channels
            await db.execute("CREATE INDEX IF NOT EXISTS idx_yt_channels_user_id ON youtube_channels(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_yt_channels_channel_id ON youtube_channels(channel_id)")
            
            # Индексы для crypto_payouts
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user ON crypto_payouts(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_video ON crypto_payouts(video_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_status ON crypto_payouts(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_created_at ON crypto_payouts(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_crypto_payouts_user_status ON crypto_payouts(user_id, status)")
            
            # Индексы для tiktok_accounts
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_user_id ON tiktok_accounts(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tiktok_accounts_username ON tiktok_accounts(username)")
            
            # Индексы для referrals
            await db.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id)")
            
            # Оптимизация настроек БД
            await db.execute("PRAGMA cache_size=-10000")  # 10MB кэш
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA temp_store=MEMORY")

            # Добавляем колонку для даты выдачи ключа (если ещё нет)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_key_issued_at TIMESTAMP")
                await db.commit()
                logger.info("✅ Добавлена колонка last_key_issued_at")
            except Exception:
                pass

            await db.commit()
            logger.info("Database initialized successfully with optimized indexes")

    # === USER METHODS ===
    async def add_user(self, user_id: int, username: str, full_name: str, referrer_id: Optional[int] = None):
        """Добавить нового пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                await db.execute(
                    "INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
                    (user_id, username, full_name, referrer_id)
                )
                await db.commit()
                
                # Если есть реферер, добавляем в таблицу рефералов
                if referrer_id:
                    await db.execute(
                        "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                        (referrer_id, user_id)
                    )
                    await db.commit()
                
                logger.info(f"User {user_id} added successfully")
                return True
            except aiosqlite.IntegrityError:
                logger.warning(f"User {user_id} already exists")
                return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_user_balance(self, user_id: int, amount: float, operation: str = 'add'):
        """
        Обновить баланс пользователя
        
        Args:
            user_id: ID пользователя
            amount: Сумма изменения
            operation: 'add' (добавить), 'subtract' (вычесть), 'set' (установить)
        """
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            if operation == 'add':
                await db.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            elif operation == 'subtract':
                await db.execute(
                    "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                    (amount, user_id)
                )
            elif operation == 'set':
                await db.execute(
                    "UPDATE users SET balance = ? WHERE user_id = ?",
                    (amount, user_id)
                )
            await db.commit()

    async def update_user_stats(self, user_id: int, videos: int = 0, views: int = 0):
        """Обновить статистику пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE users 
                   SET total_videos = total_videos + ?, 
                       total_views = total_views + ? 
                   WHERE user_id = ?""",
                (videos, views, user_id)
            )
            await db.commit()

    async def update_user_stats_withdrawal(self, user_id: int, amount: float):
        """Обновить статистику выводов пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE users 
                   SET total_withdrawn = total_withdrawn + ? 
                   WHERE user_id = ?""",
                (amount, user_id)
            )
            await db.commit()

    # === CHANNEL METHODS ===
    async def add_channel(self, user_id: int, channel_id: str, channel_name: str):
        """Добавить канал"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                await db.execute(
                    "INSERT INTO channels (user_id, channel_id, channel_name) VALUES (?, ?, ?)",
                    (user_id, channel_id, channel_name)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_user_channels(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить каналы пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM channels WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_channel_name(self, channel_id: int, new_name: str):
        """Обновить название канала"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE channels SET channel_name = ? WHERE id = ?",
                (new_name, channel_id)
            )
            await db.commit()

    async def delete_channel(self, channel_id: int):
        """Удалить канал"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
            await db.commit()

    # === VIDEO METHODS ===
    async def add_video(self, user_id: int, channel_id: int, video_url: str, 
                       video_id: Optional[str] = None, author: Optional[str] = None,
                       published_at: Optional[str] = None, views: int = 0, likes: int = 0,
                       comments: int = 0, shares: int = 0, favorites: int = 0):
        """Добавить видео с метаданными"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO videos 
                       (user_id, channel_id, video_url, tiktok_video_id, video_author, 
                        video_published_at, views, likes, comments, shares, favorites) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, channel_id, video_url, video_id, author, published_at, 
                     views, likes, comments, shares, favorites)
                )
                await db.commit()
                return cursor.lastrowid
            except aiosqlite.IntegrityError:
                # Видео с таким URL или video_id уже существует
                return None
    
    async def check_video_exists(self, video_url: str = None, video_id: str = None) -> bool:
        """Проверить, существует ли видео (по URL или TikTok ID)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            if video_url:
                async with db.execute(
                    "SELECT COUNT(*) FROM videos WHERE video_url = ?", (video_url,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] > 0
            elif video_id:
                async with db.execute(
                    "SELECT COUNT(*) FROM videos WHERE tiktok_video_id = ?", (video_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] > 0
            return False

    async def get_user_videos(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить видео пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT v.*, 
                          COALESCE(c.channel_name, yc.channel_name, ta.username, 'Канал') as channel_name
                   FROM videos v 
                   LEFT JOIN channels c ON v.channel_id = c.id 
                   LEFT JOIN youtube_channels yc ON v.youtube_channel_id = yc.id
                   LEFT JOIN tiktok_accounts ta ON v.user_id = ta.user_id AND v.platform = 'tiktok'
                   WHERE v.user_id = ? 
                   ORDER BY v.created_at DESC 
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_video_count(self, user_id: int) -> int:
        """Получить количество видео пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def update_video_stats(self, video_id: int, views: int, earnings: float):
        """Обновить статистику видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE videos 
                   SET views = ?, earnings = ? 
                   WHERE id = ?""",
                (views, earnings, video_id)
            )
            await db.commit()
    
    async def get_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Получить видео по ID"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM videos WHERE id = ?", (video_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_video_status(self, video_id: int, status: str):
        """Обновить статус видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE videos SET status = ? WHERE id = ?",
                (status, video_id)
            )
            await db.commit()

    async def update_video_earnings(self, video_id: int, earnings: float):
        """Обновить сумму выплаты за видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE videos SET earnings = ? WHERE id = ?",
                (earnings, video_id)
            )
            await db.commit()

    # === PAYMENT METHODS ===
    async def add_payment_method(self, user_id: int, method_type: str, details: str):
        """Добавить способ выплаты"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "INSERT INTO payment_methods (user_id, method_type, details) VALUES (?, ?, ?)",
                (user_id, method_type, details)
            )
            await db.commit()

    async def get_payment_methods(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить способы выплаты"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM payment_methods WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_payment_method(self, method_id: int):
        """Удалить способ выплаты"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute("DELETE FROM payment_methods WHERE id = ?", (method_id,))
            await db.commit()

    # === WITHDRAWAL METHODS ===
    async def create_withdrawal_request(self, user_id: int, amount: float, 
                                       payment_method: str, payment_details: str):
        """Создать заявку на вывод"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            cursor = await db.execute(
                """INSERT INTO withdrawal_requests 
                   (user_id, amount, payment_method, payment_details) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, amount, payment_method, payment_details)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_withdrawal_requests(self, user_id: int, limit: int = 10, 
                                     offset: int = 0) -> List[Dict[str, Any]]:
        """Получить заявки на вывод пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM withdrawal_requests 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_withdrawal_count(self, user_id: int) -> int:
        """Получить количество заявок на вывод"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM withdrawal_requests WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def process_withdrawal(self, request_id: int, success: bool):
        """Обработать заявку на вывод"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            status = "completed" if success else "rejected"
            await db.execute(
                """UPDATE withdrawal_requests 
                   SET status = ?, processed_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (status, request_id)
            )
            
            if success:
                # Получаем данные заявки
                async with db.execute(
                    "SELECT user_id, amount FROM withdrawal_requests WHERE id = ?",
                    (request_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        user_id, amount = row
                        # Списываем с баланса
                        await db.execute(
                            """UPDATE users 
                               SET balance = balance - ?, 
                                   total_withdrawn = total_withdrawn + ? 
                               WHERE user_id = ?""",
                            (amount, amount, user_id)
                        )
            
            await db.commit()

    # === REFERRAL METHODS ===
    async def get_referrals(self, referrer_id: int) -> List[Dict[str, Any]]:
        """Получить рефералов пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT r.*, u.username, u.full_name 
                   FROM referrals r 
                   JOIN users u ON r.referred_id = u.user_id 
                   WHERE r.referrer_id = ?""",
                (referrer_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_referral_stats(self, referrer_id: int) -> Dict[str, Any]:
        """Получить статистику по рефералам"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT 
                       COUNT(*) as total_referrals,
                       COALESCE(SUM(earnings), 0) as total_earnings,
                       COALESCE(AVG(earnings), 0) as avg_earnings
                   FROM referrals 
                   WHERE referrer_id = ?""",
                (referrer_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else {
                    "total_referrals": 0,
                    "total_earnings": 0,
                    "avg_earnings": 0
                }

    async def add_referral_earning(self, referrer_id: int, referred_id: int, amount: float):
        """Добавить заработок от реферала"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """
                INSERT INTO referrals (referrer_id, referred_id, earnings)
                VALUES (?, ?, ?)
                ON CONFLICT(referrer_id, referred_id)
                DO UPDATE SET earnings = referrals.earnings + excluded.earnings
                """,
                (referrer_id, referred_id, amount)
            )

            await db.execute(
                """UPDATE users 
                   SET balance = balance + ?, 
                       referral_earnings = referral_earnings + ? 
                   WHERE user_id = ?""",
                (amount, amount, referrer_id)
            )

            await db.commit()

    # === ADMIN METHODS ===
    async def get_all_withdrawal_requests(self, status: str = "pending") -> List[Dict[str, Any]]:
        """Получить все заявки на вывод (для админа)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT wr.*, u.username, u.full_name 
                   FROM withdrawal_requests wr 
                   JOIN users u ON wr.user_id = u.user_id 
                   WHERE wr.status = ? 
                   ORDER BY wr.created_at DESC""",
                (status,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Получить общую статистику (для админа)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            
            # Статистика пользователей
            async with db.execute(
                "SELECT COUNT(*) as total_users, SUM(balance) as total_balance FROM users"
            ) as cursor:
                user_stats = dict(await cursor.fetchone())
            
            # Статистика видео
            async with db.execute(
                "SELECT COUNT(*) as total_videos, SUM(views) as total_views FROM videos"
            ) as cursor:
                video_stats = dict(await cursor.fetchone())
            
            # Статистика выводов
            async with db.execute(
                """SELECT COUNT(*) as total_withdrawals, 
                          SUM(amount) as total_withdrawn 
                   FROM withdrawal_requests 
                   WHERE status = 'completed'"""
            ) as cursor:
                withdrawal_stats = dict(await cursor.fetchone())
            
            return {**user_stats, **video_stats, **withdrawal_stats}

    # === TIKTOK METHODS ===
    async def get_tiktok_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Проверить, привязан ли TikTok аккаунт (по username)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            # Убираем @ и делаем поиск без учета регистра
            clean_username = username.strip().lstrip('@').lower()
            async with db.execute(
                """SELECT ta.*, u.username as telegram_username, u.full_name 
                   FROM tiktok_accounts ta
                   JOIN users u ON ta.user_id = u.user_id
                   WHERE LOWER(ta.username) = ?""",
                (clean_username,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_tiktok(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить TikTok аккаунт пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tiktok_accounts WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def add_tiktok_account(self, user_id: int, username: str, url: str, 
                                 verification_code: str) -> Dict[str, Any]:
        """Добавить TikTok аккаунт (с проверкой уникальности)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                clean_username = username.strip().lstrip('@').lower()
                
                # Проверка 1: Привязан ли этот TikTok к другому пользователю?
                existing = await self.get_tiktok_by_username(clean_username)
                if existing:
                    return {
                        'success': False,
                        'error': 'tiktok_taken',
                        'owner_id': existing['user_id'],
                        'owner_username': existing.get('telegram_username', 'неизвестен')
                    }
                
                # Проверка 2: Есть ли у пользователя уже привязанный TikTok?
                user_tiktok = await self.get_user_tiktok(user_id)
                if user_tiktok:
                    return {
                        'success': False,
                        'error': 'user_has_tiktok',
                        'current_username': user_tiktok['username']
                    }
                
                # Добавляем новый аккаунт
                await db.execute(
                    """INSERT INTO tiktok_accounts 
                       (user_id, username, url, verification_code, is_verified)
                       VALUES (?, ?, ?, ?, 0)""",
                    (user_id, clean_username, url, verification_code)
                )
                await db.commit()
                
                return {'success': True}
                
            except aiosqlite.IntegrityError as e:
                logger.error(f"Ошибка уникальности TikTok: {e}")
                return {
                    'success': False,
                    'error': 'database_error',
                    'details': str(e)
                }

    async def verify_tiktok_account(self, user_id: int) -> bool:
        """Верифицировать TikTok аккаунт пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE tiktok_accounts 
                   SET is_verified = 1, verified_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (user_id,)
            )
            await db.commit()
            return True

    async def remove_tiktok_account(self, user_id: int) -> bool:
        """Удалить TikTok аккаунт пользователя (только админ)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            cursor = await db.execute(
                "DELETE FROM tiktok_accounts WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_all_verified_tiktoks(self) -> List[Dict[str, Any]]:
        """Получить все верифицированные TikTok аккаунты (для админа)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT ta.*, u.username as telegram_username, u.full_name
                   FROM tiktok_accounts ta
                   JOIN users u ON ta.user_id = u.user_id
                   WHERE ta.is_verified = 1
                   ORDER BY ta.verified_at DESC"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # === YOUTUBE METHODS ===
    async def get_user_youtube(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить YouTube канал пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM youtube_channels WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_youtube_by_channel_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Получить YouTube канал по channel_id"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM youtube_channels WHERE LOWER(channel_id) = LOWER(?)",
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def add_youtube_channel(self, user_id: int, channel_id: str, channel_handle: str, 
                                  channel_name: str, url: str, verification_code: str) -> Dict[str, Any]:
        """Добавить YouTube канал"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                # Проверяем, не занят ли уже этот channel_id
                existing = await self.get_youtube_by_channel_id(channel_id)
                if existing:
                    return {
                        'success': False,
                        'error': 'channel_already_bound',
                        'bound_to_user': existing['user_id']
                    }

                # Проверяем, нет ли уже YouTube у этого пользователя
                user_youtube = await self.get_user_youtube(user_id)
                if user_youtube:
                    return {
                        'success': False,
                        'error': 'user_already_has_youtube'
                    }

                # Добавляем канал
                await db.execute(
                    """INSERT INTO youtube_channels 
                       (user_id, channel_id, channel_handle, channel_name, url, verification_code)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, channel_id, channel_handle, channel_name, url, verification_code)
                )
                await db.commit()
                
                return {
                    'success': True,
                    'channel_id': channel_id
                }
                
            except aiosqlite.IntegrityError as e:
                logger.error(f"Ошибка уникальности YouTube: {e}")
                return {
                    'success': False,
                    'error': 'database_error',
                    'details': str(e)
                }

    async def verify_youtube_channel(self, user_id: int) -> bool:
        """Верифицировать YouTube канал пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                """UPDATE youtube_channels 
                   SET is_verified = 1, verified_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (user_id,)
            )
            await db.commit()
            return True

    async def remove_youtube_channel(self, user_id: int) -> bool:
        """Удалить YouTube канал пользователя (только админ)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            cursor = await db.execute(
                "DELETE FROM youtube_channels WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_all_verified_youtubes(self) -> List[Dict[str, Any]]:
        """Получить все верифицированные YouTube каналы (для админа)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT yc.*, u.username as telegram_username, u.full_name
                   FROM youtube_channels yc
                   JOIN users u ON yc.user_id = u.user_id
                   WHERE yc.is_verified = 1
                   ORDER BY yc.verified_at DESC"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== Методы для YouTube видео =====
    
    async def add_youtube_video(self, user_id: int, youtube_channel_id: int, video_url: str,
                               video_id: str, title: str, author: str, published_at: str,
                               views: int = 0, likes: int = 0, comments: int = 0) -> Optional[int]:
        """Добавить YouTube видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO videos 
                       (user_id, youtube_channel_id, platform, video_url, video_id, video_title,
                        video_author, video_published_at, views, likes, comments, status) 
                       VALUES (?, ?, 'youtube', ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
                    (user_id, youtube_channel_id, video_url, video_id, title, author,
                     published_at, views, likes, comments)
                )
                await db.commit()
                return cursor.lastrowid
            except aiosqlite.IntegrityError:
                logger.error(f"Видео уже существует: {video_url}")
                return None

    async def check_youtube_video_exists(self, video_url: str = None, video_id: str = None) -> bool:
        """Проверить, существует ли YouTube видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            if video_url:
                async with db.execute(
                    "SELECT COUNT(*) FROM videos WHERE video_url = ? AND platform = 'youtube'",
                    (video_url,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] > 0
            elif video_id:
                async with db.execute(
                    "SELECT COUNT(*) FROM videos WHERE video_id = ? AND platform = 'youtube'",
                    (video_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] > 0
            return False

    async def get_user_youtube_videos(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить YouTube видео пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT v.*, yc.channel_name 
                   FROM videos v 
                   JOIN youtube_channels yc ON v.youtube_channel_id = yc.id 
                   WHERE v.user_id = ? AND v.platform = 'youtube'
                   ORDER BY v.created_at DESC 
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_youtube_video_count(self, user_id: int) -> int:
        """Получить количество YouTube видео пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE user_id = ? AND platform = 'youtube'",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # === CRYPTO PAYOUT METHODS ===
    
    async def create_payout_request(
        self, 
        user_id: int, 
        video_id: int, 
        amount_rub: float,
        amount_usdt: float,
        spend_id: str
    ) -> Optional[int]:
        """Создать запрос на выплату"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO crypto_payouts 
                       (user_id, video_id, amount_rub, amount_usdt, spend_id, status) 
                       VALUES (?, ?, ?, ?, ?, 'pending')""",
                    (user_id, video_id, amount_rub, amount_usdt, spend_id)
                )
                await db.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Ошибка создания запроса на выплату: {e}")
                return None

    async def update_payout_status(
        self, 
        payout_id: int, 
        status: str,
        transfer_id: Optional[str] = None,
        admin_id: Optional[int] = None
    ) -> bool:
        """Обновить статус выплаты"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                if status == 'paid':
                    await db.execute(
                        """UPDATE crypto_payouts 
                           SET status = ?, transfer_id = ?, paid_at = CURRENT_TIMESTAMP, admin_id = ?
                           WHERE id = ?""",
                        (status, transfer_id, admin_id, payout_id)
                    )
                else:
                    await db.execute(
                        """UPDATE crypto_payouts 
                           SET status = ?, admin_id = ?
                           WHERE id = ?""",
                        (status, admin_id, payout_id)
                    )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления статуса выплаты: {e}")
                return False

    async def get_payout_by_id(self, payout_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о выплате"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM crypto_payouts WHERE id = ?",
                (payout_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_user_payouts(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить историю выплат пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM crypto_payouts 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def set_youtube_rate(self, user_id: int, rate: float) -> bool:
        """Установить индивидуальную ставку для YouTube канала"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                await db.execute(
                    """UPDATE youtube_channels 
                       SET rate_per_1000_views = ? 
                       WHERE user_id = ?""",
                    (rate, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка установки ставки: {e}")
                return False

    async def get_youtube_rate(self, user_id: int) -> Optional[float]:
        """Получить ставку для YouTube канала"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT rate_per_1000_views FROM youtube_channels WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def get_video_with_details(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Получить полную информацию о видео с данными канала"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            
            # Сначала получаем видео
            async with db.execute(
                "SELECT * FROM videos WHERE id = ?",
                (video_id,)
            ) as cursor:
                video = await cursor.fetchone()
                if not video:
                    return None
                
                video_dict = dict(video)
                
                # Получаем данные канала в зависимости от платформы
                if video_dict['platform'] == 'tiktok':
                    async with db.execute(
                        "SELECT * FROM tiktok_accounts WHERE user_id = ?",
                        (video_dict['user_id'],)
                    ) as cursor2:
                        channel = await cursor2.fetchone()
                        if channel:
                            video_dict['channel_info'] = dict(channel)
                
                elif video_dict['platform'] == 'youtube':
                    async with db.execute(
                        "SELECT * FROM youtube_channels WHERE user_id = ?",
                        (video_dict['user_id'],)
                    ) as cursor2:
                        channel = await cursor2.fetchone()
                        if channel:
                            video_dict['channel_info'] = dict(channel)
                
                return video_dict

    async def set_user_tier(self, user_id: int, tier: str) -> bool:
        """Установить уровень пользователя (bronze/gold)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            try:
                await db.execute(
                    "UPDATE users SET tier = ? WHERE user_id = ?",
                    (tier, user_id)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка установки уровня: {e}")
                return False

    async def get_user_tier(self, user_id: int) -> str:
        """Получить уровень пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT tier FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 'bronze'

    async def check_first_youtube_video(self, user_id: int) -> bool:
        """Проверить, первое ли это YouTube видео пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE user_id = ? AND platform = 'youtube'",
                (user_id,)
            ) as cursor:
                count = await cursor.fetchone()
                return count[0] == 1 if count else False

    async def get_last_youtube_video_time(self, user_id: int) -> Optional[str]:
        """Получить время последнего отправленного YouTube видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            async with db.execute(
                """SELECT created_at FROM videos 
                   WHERE user_id = ? AND platform = 'youtube' 
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def can_submit_youtube_video(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        Проверить, может ли пользователь отправить YouTube видео (не чаще 1 раз в 24 часа)
        
        Returns:
            tuple: (can_submit: bool, time_remaining: str)
        """
        last_video_time = await self.get_last_youtube_video_time(user_id)
        
        if not last_video_time:
            return True, None
        
        from datetime import datetime, timedelta
        
        last_time = datetime.fromisoformat(last_video_time)
        now = datetime.now()
        time_diff = now - last_time
        
        if time_diff >= timedelta(hours=24):
            return True, None
        
        # Вычисляем оставшееся время
        remaining = timedelta(hours=24) - time_diff
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        time_str = f"{hours}ч {minutes}мин"
        return False, time_str

    async def get_user_youtube_rate(self, user_id: int) -> Optional[float]:
        """Получить фиксированную ставку пользователя за YouTube видео"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            # Получаем последнее одобренное видео с установленной выплатой
            async with db.execute(
                """SELECT earnings FROM videos 
                   WHERE user_id = ? AND platform = 'youtube' AND status = 'approved' AND earnings > 0
                   ORDER BY id DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    # === ADMIN ANALYTICS METHODS ===
    async def get_admin_analytics(self, start_date, end_date) -> Dict[str, Any]:
        """Получить общую аналитику для админа"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            stats = {}
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Пользователи
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                stats['total_users'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['new_users'] = (await cursor.fetchone())[0]
            
            # Активные пользователи (с видео)
            async with db.execute(
                """SELECT COUNT(DISTINCT user_id) FROM videos 
                   WHERE created_at BETWEEN ? AND ?""",
                (start_str, end_str)
            ) as cursor:
                stats['active_users'] = (await cursor.fetchone())[0]
            
            # Видео
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['total_videos'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE status = 'approved' AND created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['approved_videos'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE status = 'pending' AND created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['pending_videos'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE status = 'rejected' AND created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['rejected_videos'] = (await cursor.fetchone())[0]
            
            # Просмотры
            async with db.execute(
                "SELECT COALESCE(SUM(views), 0) FROM videos WHERE created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['total_views'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COALESCE(SUM(views), 0) FROM videos WHERE platform = 'tiktok' AND created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['tiktok_views'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COALESCE(SUM(views), 0) FROM videos WHERE platform = 'youtube' AND created_at BETWEEN ? AND ?",
                (start_str, end_str)
            ) as cursor:
                stats['youtube_views'] = (await cursor.fetchone())[0]
            
            # Финансы (с автоматическим расчетом для TikTok)
            async with db.execute(
                """SELECT COALESCE(SUM(CASE 
                       WHEN earnings > 0 THEN earnings
                       WHEN platform = 'tiktok' THEN (views / 1000.0) * 65
                       ELSE 0
                   END), 0) 
                   FROM videos 
                   WHERE status = 'approved' AND created_at BETWEEN ? AND ?""",
                (start_str, end_str)
            ) as cursor:
                stats['total_paid'] = (await cursor.fetchone())[0]
            
            stats['total_paid_usdt'] = stats['total_paid'] / 90.0  # Фикс курс
            
            async with db.execute("SELECT COALESCE(SUM(balance), 0) FROM users") as cursor:
                stats['total_balance'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COALESCE(SUM(referral_earnings), 0) FROM users") as cursor:
                stats['referral_earnings'] = (await cursor.fetchone())[0]
            
            # Средние показатели
            stats['avg_videos_per_user'] = stats['total_videos'] / max(stats['total_users'], 1)
            stats['avg_payout'] = stats['total_paid'] / max(stats['approved_videos'], 1)
            stats['avg_views_per_video'] = stats['total_views'] / max(stats['total_videos'], 1)
            
            return stats

    async def get_top_users(self, start_date, end_date, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ пользователей по просмотрам"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            async with db.execute(
                """SELECT 
                       u.user_id, u.username, u.full_name, u.tier,
                       COUNT(DISTINCT v.id) as video_count,
                       COALESCE(SUM(v.views), 0) as total_views,
                       COALESCE(SUM(CASE 
                           WHEN v.earnings > 0 THEN v.earnings
                           WHEN v.platform = 'tiktok' THEN (v.views / 1000.0) * 65
                           ELSE 0
                       END), 0) as total_earnings,
                       (SELECT platform FROM videos 
                        WHERE user_id = u.user_id AND status = 'approved'
                        GROUP BY platform 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 1) as main_platform
                   FROM users u
                   LEFT JOIN videos v ON u.user_id = v.user_id 
                       AND v.created_at BETWEEN ? AND ?
                       AND v.status = 'approved'
                   GROUP BY u.user_id
                   HAVING video_count > 0
                   ORDER BY total_views DESC
                   LIMIT ?""",
                (start_str, end_str, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_platform_stats(self, platform: str, start_date, end_date) -> Dict[str, Any]:
        """Получить статистику по платформе"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            stats = {}
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE platform = ? AND created_at BETWEEN ? AND ?",
                (platform, start_str, end_str)
            ) as cursor:
                stats['total_videos'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM videos WHERE platform = ? AND status = 'approved' AND created_at BETWEEN ? AND ?",
                (platform, start_str, end_str)
            ) as cursor:
                stats['approved_videos'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COALESCE(SUM(views), 0) FROM videos WHERE platform = ? AND created_at BETWEEN ? AND ?",
                (platform, start_str, end_str)
            ) as cursor:
                stats['total_views'] = (await cursor.fetchone())[0]
            
            # Выплаты с автоматическим расчетом
            if platform == 'tiktok':
                async with db.execute(
                    """SELECT COALESCE(SUM(CASE 
                           WHEN earnings > 0 THEN earnings
                           ELSE (views / 1000.0) * 65
                       END), 0) 
                       FROM videos 
                       WHERE platform = ? AND status = 'approved' AND created_at BETWEEN ? AND ?""",
                    (platform, start_str, end_str)
                ) as cursor:
                    stats['total_paid'] = (await cursor.fetchone())[0]
            else:  # youtube
                async with db.execute(
                    """SELECT COALESCE(SUM(CASE 
                           WHEN earnings > 0 THEN earnings
                           ELSE 50 * (views / 1000.0)
                       END), 0)
                       FROM videos
                       WHERE platform = ? AND status = 'approved' AND created_at BETWEEN ? AND ?""",
                    (platform, start_str, end_str)
                ) as cursor:
                    stats['total_paid'] = (await cursor.fetchone())[0]
            
            return stats

    async def get_top_users_by_platform(self, platform: str, start_date, end_date, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить топ пользователей по платформе (сортировка по просмотрам)"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            db.row_factory = aiosqlite.Row
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            if platform == 'tiktok':
                async with db.execute(
                    """SELECT 
                           u.user_id, u.username, u.full_name,
                           ta.username as tiktok_username,
                           COALESCE(SUM(v.views), 0) as total_views,
                           COALESCE(SUM(CASE 
                               WHEN v.earnings > 0 THEN v.earnings
                               ELSE (v.views / 1000.0) * 65
                           END), 0) as total_earnings
                       FROM users u
                       LEFT JOIN videos v ON u.user_id = v.user_id 
                           AND v.platform = 'tiktok' 
                           AND v.status = 'approved'
                           AND v.created_at BETWEEN ? AND ?
                       LEFT JOIN tiktok_accounts ta ON u.user_id = ta.user_id
                       GROUP BY u.user_id
                       HAVING total_views > 0
                       ORDER BY total_views DESC
                       LIMIT ?""",
                    (start_str, end_str, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
            else:  # youtube
                async with db.execute(
                    """SELECT 
                           u.user_id, u.username, u.full_name,
                           yc.channel_name as youtube_channel,
                           COALESCE(SUM(v.views), 0) as total_views,
                           COALESCE(SUM(CASE 
                               WHEN v.earnings > 0 THEN v.earnings
                               ELSE 50 * (v.views / 1000.0)
                           END), 0) as total_earnings
                       FROM users u
                       LEFT JOIN videos v ON u.user_id = v.user_id 
                           AND v.platform = 'youtube' 
                           AND v.status = 'approved'
                           AND v.created_at BETWEEN ? AND ?
                       LEFT JOIN youtube_channels yc ON u.user_id = yc.user_id
                       GROUP BY u.user_id
                       HAVING total_views > 0
                       ORDER BY total_views DESC
                       LIMIT ?""",
                    (start_str, end_str, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

    async def get_finances_stats(self, start_date, end_date) -> Dict[str, Any]:
        """Получить финансовую статистику с автоматическим расчетом"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            stats = {}
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Общие выплаты (с автоматическим расчетом для TikTok)
            async with db.execute(
                """SELECT 
                       COALESCE(SUM(CASE 
                           WHEN earnings > 0 THEN earnings
                           WHEN platform = 'tiktok' THEN (views / 1000.0) * 65
                           ELSE 0
                       END), 0) as total,
                       COUNT(*) as count
                   FROM videos 
                   WHERE status = 'approved' AND created_at BETWEEN ? AND ?""",
                (start_str, end_str)
            ) as cursor:
                row = await cursor.fetchone()
                stats['total_paid'] = row[0]
                stats['payout_count'] = row[1]
            
            stats['total_paid_usdt'] = stats['total_paid'] / 90.0
            
            # Балансы
            async with db.execute("SELECT COALESCE(SUM(balance), 0) FROM users") as cursor:
                stats['total_balance'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COALESCE(SUM(referral_earnings), 0) FROM users") as cursor:
                stats['referral_earnings'] = (await cursor.fetchone())[0]
            
            # По платформам (с автоматическим расчетом)
            async with db.execute(
                """SELECT COALESCE(SUM(CASE 
                       WHEN earnings > 0 THEN earnings
                       ELSE (views / 1000.0) * 65
                   END), 0) 
                   FROM videos 
                   WHERE platform = 'tiktok' AND status = 'approved' AND created_at BETWEEN ? AND ?""",
                (start_str, end_str)
            ) as cursor:
                stats['tiktok_paid'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                """SELECT COALESCE(SUM(CASE 
                       WHEN earnings > 0 THEN earnings
                       ELSE 50 * (views / 1000.0)
                   END), 0)
                   FROM videos 
                   WHERE platform = 'youtube' AND status = 'approved' AND created_at BETWEEN ? AND ?""",
                (start_str, end_str)
            ) as cursor:
                stats['youtube_paid'] = (await cursor.fetchone())[0]
            
            # Средние показатели
            stats['avg_payout'] = stats['total_paid'] / max(stats['payout_count'], 1)
            
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                user_count = (await cursor.fetchone())[0]
            stats['avg_per_user'] = stats['total_paid'] / max(user_count, 1)
            
            return stats

    async def ban_user(self, user_id: int):
        """Забанить пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET tier = 'banned' WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def unban_user(self, user_id: int):
        """Разбанить пользователя"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute(
                "UPDATE users SET tier = 'bronze' WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
