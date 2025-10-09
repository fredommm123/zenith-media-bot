import asyncio
import logging
from datetime import datetime
from typing import List, Tuple

from aiogram import Bot

from core.database import Database
from core.utils import send_to_admin_chat
from core import config

logger = logging.getLogger(__name__)


class MediaKeyDistributor:
    """Автоматическая выдача ключей медиапартнёрам"""

    def __init__(
        self,
        db_path: str,
        min_videos: int = 2,
        period_days: int = 7,
        interval_hours: int = 24,
    ):
        self.db = Database(db_path)
        self.min_videos = min_videos
        self.period_days = period_days
        self.interval = interval_hours * 3600
        self._running = False

    async def start_auto_distribution(self, bot: Bot):
        """Запустить фоновую задачу автоматической выдачи"""
        if self._running:
            logger.warning("MediaKeyDistributor already running")
            return

        self._running = True
        logger.info(
            "🔑 Автовыдача ключей запущена (интервал: %.1f часов)",
            self.interval / 3600,
        )

        while self._running:
            try:
                await self.distribute(bot)
            except Exception as exc:
                logger.exception("Ошибка при автоматической выдаче ключей: %s", exc)
            finally:
                await asyncio.sleep(self.interval)

    def stop(self):
        """Остановить цикл выдачи"""
        self._running = False

    async def distribute(self, bot: Bot):
        """Выполнить одну итерацию выдачи ключей"""
        eligible_users = await self.db.get_users_for_key_distribution(
            self.min_videos, self.period_days
        )

        if not eligible_users:
            logger.info("Нет пользователей, удовлетворяющих условиям выдачи ключей")
            return

        available_keys = await self.db.count_available_media_keys()
        if available_keys <= 0:
            logger.warning("Нет доступных ключей для выдачи")
            await send_to_admin_chat(
                bot,
                "⚠️ <b>Недостаточно ключей</b>\n"
                "Нет доступных ключей для автоматической выдачи.\n"
                "Загрузите новые ключи через админ-панель.",
            )
            return

        assigned: List[Tuple[dict, dict]] = []

        for user in eligible_users:
            if available_keys <= 0:
                logger.info("Ключи закончились, остановка выдачи")
                break

            key = await self.db.get_next_available_media_key()
            if not key:
                logger.info("Свободные ключи закончились")
                break

            await self.db.mark_media_key_assigned(key["id"], user["user_id"])
            await self.db.update_user_last_key_issued(user["user_id"], datetime.utcnow())

            available_keys -= 1
            assigned.append((user, key))

            await self._notify_user(bot, user, key)

        if assigned:
            await self._notify_admin(bot, assigned)
        else:
            logger.info("Никому не удалось выдать ключи в этот цикл")

    async def _notify_user(self, bot: Bot, user: dict, key: dict):
        text = (
            "🔑 <b>Новый ключ партнёра</b>\n\n"
            f"Ваш прогресс за последние {self.period_days} дней впечатляет!\n"
            f"Ключ для интеграции:\n<code>{key['key_value']}</code>\n\n"
            "Не передавайте его третьим лицам."
        )
        try:
            await bot.send_message(user["user_id"], text, parse_mode="HTML")
        except Exception as exc:
            logger.error(
                "Не удалось отправить ключ пользователю %s: %s",
                user["user_id"],
                exc,
            )

    async def _notify_admin(self, bot: Bot, assigned: List[Tuple[dict, dict]]):
        lines = [
            "✅ <b>Выдача ключей выполнена</b>",
            f"📅 Период: последние {self.period_days} дней",
            f"👥 Пользователей: {len(assigned)}",
            "",
        ]
        for user, key in assigned:
            username = user.get("username") or f"user_{user['user_id']}"
            lines.append(
                f"🔑 <code>{key['key_value']}</code> → {user['user_id']} (@{username})\n"
                f"   Видео за период: {user.get('videos_count', 0)}"
            )

        await send_to_admin_chat(bot, "\n".join(lines))


media_key_manager = MediaKeyDistributor(db_path=config.DATABASE_PATH)
