"""
Админ-панель с расширенной аналитикой и управлением
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database import Database
from core import config
from core.keyboards import (
    admin_panel_keyboard,
    admin_time_filter_keyboard,
    admin_user_actions_keyboard,
    admin_media_keys_keyboard,
    cancel_keyboard
)

router = Router()
db = Database(config.DATABASE_PATH)
logger = logging.getLogger(__name__)


class MediaKeysStates(StatesGroup):
    waiting_for_upload = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав админа"""
    return user_id in config.ADMIN_IDS


def get_date_range(period: str):
    """Получить диапазон дат для фильтра"""
    now = datetime.now()
    
    if period == "today":
        start = datetime(now.year, now.month, now.day)
        end = now
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start = datetime(yesterday.year, yesterday.month, yesterday.day)
        end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    elif period == "week":
        start = now - timedelta(days=7)
        end = now
    elif period == "month":
        start = now - timedelta(days=30)
        end = now
    else:  # all
        start = datetime(2020, 1, 1)
        end = now
    
    return start, end


@router.message(F.text == "👨‍💼 Админ-панель")
async def show_admin_panel(message: Message):
    """Показать главное меню админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    text = (
        "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Выберите раздел для управления:"
    )
    
    await message.answer(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    """Вернуться в главное меню админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    text = (
        "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Выберите раздел для управления:"
    )
    
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_analytics")
async def show_analytics(callback: CallbackQuery):
    """Показать общую аналитику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📊 <b>Выберите период:</b>",
        reply_markup=admin_time_filter_keyboard("analytics"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("analytics_"))
async def show_analytics_period(callback: CallbackQuery):
    """Показать аналитику за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    start_date, end_date = get_date_range(period)
    
    # Получаем статистику
    stats = await db.get_admin_analytics(start_date, end_date)
    
    period_names = {
        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }
    
    text = (
        f"📊 <b>ОБЩАЯ АНАЛИТИКА</b>\n"
        f"📅 Период: {period_names.get(period, 'Неизвестно')}\n\n"
        
        f"👥 <b>Пользователи:</b>\n"
        f"  • Всего: {stats['total_users']}\n"
        f"  • Новых: {stats['new_users']}\n"
        f"  • Активных: {stats['active_users']}\n\n"
        
        f"📹 <b>Видео:</b>\n"
        f"  • Всего: {stats['total_videos']}\n"
        f"  • Одобрено: {stats['approved_videos']}\n"
        f"  • На модерации: {stats['pending_videos']}\n"
        f"  • Отклонено: {stats['rejected_videos']}\n\n"
        
        f"👁 <b>Просмотры:</b>\n"
        f"  • Всего: {stats['total_views']:,}\n"
        f"  • TikTok: {stats['tiktok_views']:,}\n"
        f"  • YouTube: {stats['youtube_views']:,}\n\n"
        
        f"💰 <b>Финансы:</b>\n"
        f"  • Выплачено: {stats['total_paid']:.2f} ₽\n"
        f"  • В USDT: ~{stats['total_paid_usdt']:.4f}\n"
        f"  • На балансах: {stats['total_balance']:.2f} ₽\n"
        f"  • Реф. доход: {stats['referral_earnings']:.2f} ₽\n\n"
        
        f"🎯 <b>Средние показатели:</b>\n"
        f"  • Видео на юзера: {stats['avg_videos_per_user']:.1f}\n"
        f"  • Выплата: {stats['avg_payout']:.2f} ₽\n"
        f"  • Просмотров на видео: {stats['avg_views_per_video']:,.0f}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_time_filter_keyboard("analytics"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_top_users")
async def show_top_users(callback: CallbackQuery):
    """Показать топ пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🏆 <b>Выберите период:</b>",
        reply_markup=admin_time_filter_keyboard("top"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("top_"))
async def show_top_users_period(callback: CallbackQuery):
    """Показать топ пользователей за период (разделено по платформам)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    start_date, end_date = get_date_range(period)
    
    # Получаем топ по платформам
    top_tiktokers = await db.get_top_users_by_platform('tiktok', start_date, end_date, limit=5)
    top_youtubers = await db.get_top_users_by_platform('youtube', start_date, end_date, limit=5)
    
    period_names = {
        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }
    
    text = (
        f"🏆 <b>ТОП ПОЛЬЗОВАТЕЛЕЙ</b>\n"
        f"📅 Период: {period_names.get(period, 'Неизвестно')}\n\n"
    )
    
    # Топ TikTokers
    text += "🎵 <b>ТОП TIKTOK:</b>\n\n"
    if not top_tiktokers:
        text += "Нет данных\n\n"
    else:
        for i, user in enumerate(top_tiktokers, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            text += (
                f"{emoji} <b>#{i}</b> {user['full_name']}\n"
                f"  • @{user.get('tiktok_username', user.get('username', 'нет'))}\n"
                f"  • 👁 {user['total_views']:,} просмотров\n"
                f"  • 💰 {user['total_earnings']:.2f} ₽\n\n"
            )
    
    # Топ YouTubers
    text += "📺 <b>ТОП YOUTUBE:</b>\n\n"
    if not top_youtubers:
        text += "Нет данных"
    else:
        for i, user in enumerate(top_youtubers, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            text += (
                f"{emoji} <b>#{i}</b> {user['full_name']}\n"
                f"  • {user.get('youtube_channel', user.get('username', 'нет'))}\n"
                f"  • 👁 {user['total_views']:,} просмотров\n"
                f"  • 💰 {user['total_earnings']:.2f} ₽\n\n"
            )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_time_filter_keyboard("top"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_media_keys")
async def show_media_keys_menu(callback: CallbackQuery):
    """Меню управления ключами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    available = await db.count_available_media_keys()

    text = (
        "🔑 <b>УПРАВЛЕНИЕ КЛЮЧАМИ</b>\n\n"
        f"📦 Доступно ключей: <b>{available}</b>\n"
        "• Загружайте наборы ключей (по одному в строке).\n"
        "• Автовыдача проходит раз в 7 дней для активных партнёров."
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_media_keys_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_media_keys_upload")
async def prompt_keys_upload(callback: CallbackQuery, state: FSMContext):
    """Запросить у админа загрузку ключей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await state.set_state(MediaKeysStates.waiting_for_upload)
    await callback.message.edit_text(
        "📥 <b>Загрузка ключей</b>\n\n"
        "Отправьте файл .txt или список ключей текстом, по одному на строку.",
        reply_markup=cancel_keyboard("admin_media_keys"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(MediaKeysStates.waiting_for_upload)
async def receive_media_keys(message: Message, state: FSMContext):
    """Приём ключей от администратора"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав!", parse_mode="HTML")
        return

    keys: list[str] = []

    if message.document:
        document = message.document
        if not document.file_name.endswith('.txt'):
            await message.answer(
                "❌ Неверный формат файла. Загрузите .txt", parse_mode="HTML"
            )
            return
        file = await message.bot.download(document)
        content = file.read().decode('utf-8')
        keys = content.splitlines()
    elif message.text:
        keys = message.text.splitlines()
    else:
        await message.answer(
            "❌ Не удалось прочитать ключи. Отправьте текст или .txt файл.",
            parse_mode="HTML"
        )
        return

    inserted = await db.add_media_keys(keys, uploaded_by=message.from_user.id)
    await state.clear()

    await message.answer(
        f"✅ Загружено ключей: <b>{inserted}</b>",
        reply_markup=admin_media_keys_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_media_keys_recent")
async def show_recent_keys(callback: CallbackQuery):
    """Показать последние выдачи ключей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    recent = await db.get_recently_assigned_media_keys(limit=10)

    if not recent:
        text = "ℹ️ Пока нет выданных ключей."
    else:
        lines = ["📄 <b>Последние выдачи</b>:\n"]
        for item in recent:
            user_display = item.get('assigned_username') or item.get('assigned_to') or '—'
            assigned_at = item.get('assigned_at') or '—'
            lines.append(
                f"🔑 <code>{item['key_value']}</code>\n"
                f"   👤 {user_display}\n"
                f"   📅 {assigned_at}\n"
            )
        text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=admin_media_keys_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_user_management")
async def show_user_management(callback: CallbackQuery):
    """Показать меню управления пользователями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    text = (
        "👥 <b>УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ</b>\n\n"
        "Отправьте ID пользователя для управления.\n"
        "Пример: <code>123456789</code>"
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ban_"))
async def ban_user(callback: CallbackQuery):
    """Забанить пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[2])
    
    # Устанавливаем статус banned
    await db.ban_user(user_id)
    
    await callback.answer(f"✅ Пользователь {user_id} забанен!", show_alert=True)
    await callback.message.edit_text(
        f"🚫 <b>Пользователь забанен</b>\n\n"
        f"ID: {user_id}\n"
        f"Статус: BANNED",
        reply_markup=admin_user_actions_keyboard(user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_unban_"))
async def unban_user(callback: CallbackQuery):
    """Разбанить пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[2])
    
    # Снимаем статус banned
    await db.unban_user(user_id)
    
    await callback.answer(f"✅ Пользователь {user_id} разбанен!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>Пользователь разбанен</b>\n\n"
        f"ID: {user_id}\n"
        f"Статус: ACTIVE",
        reply_markup=admin_user_actions_keyboard(user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_reset_balance_"))
async def reset_balance(callback: CallbackQuery):
    """Обнулить баланс пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[3])
    
    # Получаем текущий баланс
    user = await db.get_user(user_id)
    old_balance = user.get('balance', 0) if user else 0
    
    # Обнуляем баланс
    await db.update_user_balance(user_id, 0, operation='set')
    
    await callback.answer(f"✅ Баланс обнулен! Было: {old_balance:.2f} ₽", show_alert=True)
    await callback.message.edit_text(
        f"💸 <b>Баланс обнулен</b>\n\n"
        f"ID: {user_id}\n"
        f"Было: {old_balance:.2f} ₽\n"
        f"Стало: 0.00 ₽",
        reply_markup=admin_user_actions_keyboard(user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_tiktok_stats")
async def show_tiktok_stats(callback: CallbackQuery):
    """Показать статистику TikTok"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🎵 <b>Выберите период:</b>",
        reply_markup=admin_time_filter_keyboard("tiktok"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tiktok_"))
async def show_tiktok_stats_period(callback: CallbackQuery):
    """Показать статистику TikTok за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    start_date, end_date = get_date_range(period)
    
    stats = await db.get_platform_stats('tiktok', start_date, end_date)
    top_tiktokers = await db.get_top_users_by_platform('tiktok', start_date, end_date, limit=5)
    
    period_names = {
        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }
    
    text = (
        f"🎵 <b>СТАТИСТИКА TIKTOK</b>\n"
        f"📅 Период: {period_names.get(period, 'Неизвестно')}\n\n"
        
        f"📊 <b>Общая статистика:</b>\n"
        f"  • Видео: {stats['total_videos']}\n"
        f"  • Одобрено: {stats['approved_videos']}\n"
        f"  • Просмотры: {stats['total_views']:,}\n"
        f"  • Выплачено: {stats['total_paid']:.2f} ₽\n\n"
        
        f"🏆 <b>Топ TikTokers:</b>\n"
    )
    
    if top_tiktokers:
        for i, user in enumerate(top_tiktokers, 1):
            text += (
                f"  {i}. @{user.get('tiktok_username', 'нет')}\n"
                f"     👁 {user['total_views']:,} | 💰 {user['total_earnings']:.2f} ₽\n"
            )
    else:
        text += "  Нет данных\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_time_filter_keyboard("tiktok"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_youtube_stats")
async def show_youtube_stats(callback: CallbackQuery):
    """Показать статистику YouTube"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📺 <b>Выберите период:</b>",
        reply_markup=admin_time_filter_keyboard("youtube"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("youtube_"))
async def show_youtube_stats_period(callback: CallbackQuery):
    """Показать статистику YouTube за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    start_date, end_date = get_date_range(period)
    
    stats = await db.get_platform_stats('youtube', start_date, end_date)
    top_youtubers = await db.get_top_users_by_platform('youtube', start_date, end_date, limit=5)
    
    period_names = {
        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }
    
    text = (
        f"📺 <b>СТАТИСТИКА YOUTUBE</b>\n"
        f"📅 Период: {period_names.get(period, 'Неизвестно')}\n\n"
        
        f"📊 <b>Общая статистика:</b>\n"
        f"  • Видео: {stats['total_videos']}\n"
        f"  • Одобрено: {stats['approved_videos']}\n"
        f"  • Просмотры: {stats['total_views']:,}\n"
        f"  • Выплачено: {stats['total_paid']:.2f} ₽\n\n"
        
        f"🏆 <b>Топ YouTubers:</b>\n"
    )
    
    if top_youtubers:
        for i, user in enumerate(top_youtubers, 1):
            text += (
                f"  {i}. @{user.get('youtube_channel', 'нет')}\n"
                f"     👁 {user['total_views']:,} | 💰 {user['total_earnings']:.2f} ₽\n"
            )
    else:
        text += "  Нет данных\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_time_filter_keyboard("youtube"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_finances")
async def show_finances(callback: CallbackQuery):
    """Показать финансовую статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💰 <b>Выберите период:</b>",
        reply_markup=admin_time_filter_keyboard("finances"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("finances_"))
async def show_finances_period(callback: CallbackQuery):
    """Показать финансы за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    start_date, end_date = get_date_range(period)
    
    finances = await db.get_finances_stats(start_date, end_date)
    
    period_names = {
        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }
    
    text = (
        f"💰 <b>ФИНАНСОВАЯ СТАТИСТИКА</b>\n"
        f"📅 Период: {period_names.get(period, 'Неизвестно')}\n\n"
        
        f"💸 <b>Выплаты:</b>\n"
        f"  • Всего выплачено: {finances['total_paid']:.2f} ₽\n"
        f"  • В USDT: ~{finances['total_paid_usdt']:.4f}\n"
        f"  • Кол-во выплат: {finances['payout_count']}\n\n"
        
        f"💼 <b>Балансы:</b>\n"
        f"  • На балансах юзеров: {finances['total_balance']:.2f} ₽\n"
        f"  • Реф. доход: {finances['referral_earnings']:.2f} ₽\n\n"
        
        f"📊 <b>Статистика по платформам:</b>\n"
        f"  • TikTok: {finances['tiktok_paid']:.2f} ₽\n"
        f"  • YouTube: {finances['youtube_paid']:.2f} ₽\n\n"
        
        f"🎯 <b>Средние показатели:</b>\n"
        f"  • Средняя выплата: {finances['avg_payout']:.2f} ₽\n"
        f"  • На юзера: {finances['avg_per_user']:.2f} ₽"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_time_filter_keyboard("finances"),
        parse_mode="HTML"
    )
    await callback.answer()
