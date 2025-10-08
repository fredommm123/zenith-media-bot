from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from core.database import Database
from core.keyboards import (
    canc        # Проверяем статус пользователя (Gold = автоодобрение)
        user = await db.get_user(message.from_user.id)
        is_gold = user and user.get('tier') == 'gold'
        
        if is_gold:
            # Для GOLD пользователей - автоматическое одобрение
            await db.update_video_status(saved_video_id, 'approved')
            
            # Рассчитываем выплату
            from core.config import TIKTOK_RATE_PER_1000_VIEWS
            earnings = (video_data['views'] / 1000) * TIKTOK_RATE_PER_1000_VIEWS
            await db.update_video_earnings(saved_video_id, earnings)
            
            # Кнопка для получения выплаты
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            payout_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Получить выплату", callback_data=f"get_payout_{saved_video_id}")]
            ])
            
            await message.answer(
                f"✅ <b>TikTok видео автоматически одобрено!</b>\n\n"
                f"🆔 ID заявки: <code>{saved_video_id}</code>\n"
                f"🎵 Автор: <code>@{video_data['author']}</code>\n"
                f"📅 Опубликовано: {published_str}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"👁 Просмотры: {video_data['views']:,}\n"
                f"❤️ Лайки: {video_data['likes']:,}\n"
                f"💬 Комментарии: {video_data['comments']:,}\n"
                f"🔄 Репосты: {video_data['shares']:,}\n"
                f"⭐ Избранные: {video_data['favorites']:,}\n\n"
                f"💰 <b>Выплата: {earnings:.2f} ₽</b>\n\n"
                f"🌟 Статус GOLD - видео одобрено автоматически!",
                reply_markup=payout_keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"✅ <b>TikTok видео успешно добавлено!</b>\n\n"
                f"🆔 ID заявки: <code>{saved_video_id}</code>\n"
                f"🎵 Автор: <code>@{video_data['author']}</code>\n"
                f"📅 Опубликовано: {published_str}\n\n"
                f"📊 <b>Статистика на момент подачи:</b>\n"
                f"👁 Просмотры: {video_data['views']:,}\n"
                f"❤️ Лайки: {video_data['likes']:,}\n"
                f"💬 Комментарии: {video_data['comments']:,}\n"
                f"🔄 Репосты: {video_data['shares']:,}\n"
                f"⭐ Избранные: {video_data['favorites']:,}\n\n"
                f"⏳ Заявка отправлена на модерацию.\n"
                f"После одобрения начнется подсчет просмотров для выплат.",
                parse_mode="HTML"
            )
        
        # Уведомляем администраторов с кнопками управления
        from core.keyboards import video_moderation_keyboard
        from core.utils import send_to_admin_chatagination_keyboard
)
from core.utils import format_currency, format_timestamp, get_status_emoji, get_status_text, calculate_pages
from parsers.tiktok_parser import validate_tiktok_video, extract_tiktok_video_id
from core import config

router = Router()
db = Database(config.DATABASE_PATH)


def create_progress_bar(percent: int) -> str:
    """Создает прогресс-бар визуально"""
    filled = int(percent / 10)
    empty = 10 - filled
    return f"{'🟩' * filled}{'⬜' * empty} {percent}%"


async def update_progress_message(message: Message, title: str, steps: list, current_step: int, total_steps: int):
    """Обновляет сообщение с прогресс-баром"""
    percent = int((current_step / total_steps) * 100)
    progress_bar = create_progress_bar(percent)
    
    text = f"🔍 <b>{title}</b>\n\n{progress_bar}\n\n"
    
    for i, step in enumerate(steps):
        if i < current_step:
            text += f"✅ {step}\n"
        elif i == current_step:
            text += f"⏳ {step}\n"
        else:
            text += f"⏸️ {step}\n"
    
    try:
        await message.edit_text(text, parse_mode="HTML")
    except:
        pass


class VideoStates(StatesGroup):
    waiting_for_video_url = State()


@router.callback_query(F.data == "submit_tiktok_video")
async def submit_tiktok_video_callback(callback: CallbackQuery, state: FSMContext):
    """Подача TikTok видео"""
    tiktok = await db.get_user_tiktok(callback.from_user.id)
    
    if not tiktok or not tiktok.get('is_verified'):
        await callback.answer("❌ TikTok не привязан или не верифицирован!", show_alert=True)
        return
    
    await state.set_state(VideoStates.waiting_for_video_url)
    await state.update_data(platform='tiktok')
    
    await callback.message.edit_text(
        "🎬 <b>Подача TikTok ролика</b>\n\n"
        f"🎵 Ваш TikTok: <code>@{tiktok['username']}</code>\n\n"
        "📋 <b>Требования:</b>\n"
        "✅ Видео с вашего TikTok аккаунта\n"
        "✅ Опубликовано не позже 24 часов назад\n"
        "✅ Не было отправлено ранее\n\n"
        "🔗 Отправьте ссылку на ваш TikTok ролик:\n"
        "Например: <code>https://www.tiktok.com/@username/video/123...</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(F.text == "🎬 Подать ролик")
async def submit_video_start(message: Message, state: FSMContext):
    """Начать подачу ролика - выбор платформы"""
    from core.keyboards import video_platform_keyboard
    
    # Проверяем привязанные платформы
    tiktok = await db.get_user_tiktok(message.from_user.id)
    youtube = await db.get_user_youtube(message.from_user.id)
    
    has_tiktok = tiktok and tiktok.get('is_verified', False)
    has_youtube = youtube and youtube.get('is_verified', False)
    
    if not has_tiktok and not has_youtube:
        await message.answer(
            "❌ <b>У вас нет привязанных платформ!</b>\n\n"
            "Сначала привяжите TikTok или YouTube через профиль.",
            parse_mode="HTML"
        )
        return
    
    platforms_text = "📱 <b>Выберите платформу:</b>\n\n"
    
    if has_tiktok:
        platforms_text += f"🎵 <b>TikTok:</b> @{tiktok['username']}\n"
    
    if has_youtube:
        platforms_text += f"📺 <b>YouTube:</b> {youtube['channel_name']}\n"
    
    await message.answer(
        platforms_text,
        reply_markup=video_platform_keyboard(has_tiktok=has_tiktok, has_youtube=has_youtube),
        parse_mode="HTML"
    )


@router.message(VideoStates.waiting_for_video_url)
async def submit_video_url(message: Message, state: FSMContext):
    """Получить ссылку на TikTok ролик и провалидировать"""
    video_url = message.text.strip()
    
    # Нормализуем URL - добавляем https:// если отсутствует
    if not video_url.startswith(('http://', 'https://')):
        if video_url.startswith('www.'):
            video_url = 'https://' + video_url
        elif video_url.startswith(('tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com')):
            video_url = 'https://' + video_url
        else:
            video_url = 'https://www.' + video_url
    
    # Проверка формата ссылки
    if not ('tiktok.com' in video_url.lower() or 'vm.tiktok.com' in video_url.lower() or 'vt.tiktok.com' in video_url.lower()):
        await message.answer(
            "❌ <b>Неверный формат ссылки!</b>\n\n"
            "Отправьте ссылку на TikTok видео:\n"
            "• <code>https://www.tiktok.com/@username/video/123...</code>\n"
            "• <code>https://vm.tiktok.com/abc...</code>\n\n"
            "Или просто:\n"
            "• <code>tiktok.com/@username/video/123...</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Извлекаем video_id для проверки дубликатов
    video_id = extract_tiktok_video_id(video_url)
    if not video_id:
        await message.answer(
            "❌ <b>Не удалось извлечь ID видео из ссылки</b>\n\n"
            "Убедитесь, что ссылка корректна.",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Проверка 1: Дубликат (уже отправлено)
    if await db.check_video_exists(video_url=video_url) or await db.check_video_exists(video_id=video_id):
        await message.answer(
            "❌ <b>Это видео уже было отправлено ранее!</b>\n\n"
            "Каждое видео можно отправить только один раз.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Получаем TikTok аккаунт пользователя
    tiktok = await db.get_user_tiktok(message.from_user.id)
    if not tiktok or not tiktok['is_verified']:
        await message.answer(
            "❌ У вас нет верифицированного TikTok аккаунта!",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Показываем прогресс проверки видео
    steps = [
        "Подключение к TikTok",
        "Парсинг метаданных видео",
        "Проверка автора",
        "Проверка даты публикации"
    ]
    
    parsing_msg = await message.answer(
        "🔍 <b>Проверка видео...</b>\n\n"
        "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%\n\n"
        "⏳ Подключение к TikTok\n"
        "⏸️ Парсинг метаданных видео\n"
        "⏸️ Проверка автора\n"
        "⏸️ Проверка даты публикации",
        parse_mode="HTML"
    )
    
    try:
        # Шаг 1: Подключение
        await asyncio.sleep(0.5)
        await update_progress_message(parsing_msg, "Проверка видео...", steps, 1, 4)
        
        # Шаг 2-4: Валидация видео
        await update_progress_message(parsing_msg, "Проверка видео...", steps, 2, 4)
        validation = await validate_tiktok_video(video_url, tiktok['username'])
        
        await update_progress_message(parsing_msg, "Проверка видео...", steps, 3, 4)
        await asyncio.sleep(0.3)
        
        # Завершено
        await parsing_msg.delete()
        
        if not validation['success']:
            error_code = validation.get('error_code')
            error_msg = validation.get('error')
            
            if error_code == 'wrong_author':
                await message.answer(
                    f"❌ <b>Видео с чужого аккаунта!</b>\n\n"
                    f"{error_msg}\n\n"
                    f"✅ Ваш TikTok: <code>@{tiktok['username']}</code>\n"
                    f"❌ Автор видео: <code>@{validation.get('video_data', {}).get('author', 'неизвестен')}</code>",
                    parse_mode="HTML"
                )
            elif error_code == 'too_old':
                await message.answer(
                    f"❌ <b>Видео слишком старое!</b>\n\n"
                    f"{error_msg}\n\n"
                    f"⏰ Принимаются только видео не старше 24 часов.",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    f"❌ <b>Ошибка проверки видео</b>\n\n"
                    f"{error_msg}",
                    parse_mode="HTML"
                )
            
            await state.clear()
            return
        
        # Все проверки пройдены! Сохраняем видео
        video_data = validation['video_data']
        
        # Сохраняем в БД (channel_id = 0 для TikTok, не используем старую таблицу channels)
        saved_video_id = await db.add_video(
            user_id=message.from_user.id,
            channel_id=0,  # Для TikTok не используем channels
            video_url=video_url,
            video_id=video_data['video_id'],
            author=video_data['author'],
            published_at=video_data['published_at'].isoformat() if video_data['published_at'] else None,
            views=video_data['views'],
            likes=video_data['likes'],
            comments=video_data['comments'],
            shares=video_data['shares'],
            favorites=video_data['favorites']
        )
        
        if not saved_video_id:
            await message.answer(
                "❌ <b>Ошибка сохранения видео</b>\n\n"
                "Возможно, это видео уже было добавлено.",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Обновляем статистику пользователя
        await db.update_user_stats(message.from_user.id, videos=1)
        
        # Успешно добавлено!
        published_str = video_data['published_at'].strftime('%d.%m.%Y %H:%M') if video_data['published_at'] else 'неизвестно'
        
        await message.answer(
            f"✅ <b>TikTok видео успешно добавлено!</b>\n\n"
            f"🆔 ID заявки: <code>{saved_video_id}</code>\n"
            f"🎵 Автор: <code>@{video_data['author']}</code>\n"
            f"📅 Опубликовано: {published_str}\n\n"
            f"� <b>Статистика на момент подачи:</b>\n"
            f"👁 Просмотры: {video_data['views']:,}\n"
            f"❤️ Лайки: {video_data['likes']:,}\n"
            f"💬 Комментарии: {video_data['comments']:,}\n"
            f"🔄 Репосты: {video_data['shares']:,}\n"
            f"⭐ Избранные: {video_data['favorites']:,}\n\n"
            f"⏳ Заявка отправлена на модерацию.\n"
            f"После одобрения начнется подсчет просмотров для выплат.",
            parse_mode="HTML"
        )
        
        # Уведомляем администраторов
        from core.keyboards import video_moderation_keyboard
        from core.utils import send_to_admin_chat
        
        if is_gold:
            # Для GOLD - уведомление об автоодобрении
            from core.config import TIKTOK_RATE_PER_1000_VIEWS
            earnings = (video_data['views'] / 1000) * TIKTOK_RATE_PER_1000_VIEWS
            await send_to_admin_chat(
                message.bot,
                f"🌟 <b>GOLD: Видео автоматически одобрено</b>\n\n"
                f"� {message.from_user.full_name} (@{message.from_user.username})\n"
                f"🆔 Video ID: <code>{saved_video_id}</code>\n\n"
                f"🎵 TikTok: <code>@{video_data['author']}</code>\n"
                f"📅 Опубликовано: {published_str}\n"
                f"👁 Просмотры: {video_data['views']:,}\n"
                f"💰 Выплата: {earnings:.2f} ₽\n"
                f"🔗 {video_url}"
            )
        else:
            # Для обычных - на модерацию
            await send_to_admin_chat(
                message.bot,
                f"�🔔 <b>Новое TikTok видео на модерацию</b>\n\n"
                f"👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
                f"🆔 User ID: <code>{message.from_user.id}</code>\n"
                f"🆔 Video ID: <code>{saved_video_id}</code>\n\n"
                f"🎵 TikTok: <code>@{video_data['author']}</code>\n"
                f"📅 Опубликовано: {published_str}\n"
                f"🔗 Ссылка: {video_url}\n\n"
                f"📊 Статистика:\n"
                f"👁 {video_data['views']:,} | ❤️ {video_data['likes']:,} | "
                f"💬 {video_data['comments']:,} | 🔄 {video_data['shares']:,}",
                reply_markup=video_moderation_keyboard(saved_video_id)
            )
        
        await state.clear()
        
    except Exception as e:
        await parsing_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка при обработке видео</b>\n\n"
            f"Технические детали: {str(e)[:200]}\n\n"
            f"Попробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML"
        )
        await state.clear()


@router.message(F.text == "📜 История")
async def show_history(message: Message):
    """Показать историю заявок"""
    await show_history_page(message, page=1)


async def show_history_page(message: Message, page: int = 1):
    """Показать страницу истории"""
    items_per_page = 5
    offset = (page - 1) * items_per_page
    
    videos = await db.get_user_videos(message.from_user.id, limit=items_per_page, offset=offset)
    total_videos = await db.get_video_count(message.from_user.id)
    total_pages = calculate_pages(total_videos, items_per_page)
    
    if not videos:
        await message.answer(
            "📭 <b>История заявок пуста</b>\n\n"
            "У вас пока нет поданных роликов.",
            parse_mode="HTML"
        )
        return
    
    history_text = f"📜 <b>История заявок</b>\n\n"
    
    for video in videos:
        status_emoji = get_status_emoji(video['status'])
        status_text = get_status_text(video['status'])
        created_at = format_timestamp(video['created_at'])
        
        # Показываем TikTok автора вместо канала
        author_display = f"@{video['video_author']}" if video.get('video_author') else video.get('channel_name', 'TikTok')
        
        history_text += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{video['id']}</code>\n"
            f"🎵 Автор: <code>{author_display}</code>\n"
            f"🔗 Ссылка: {video['video_url'][:50]}...\n"
            f"📊 Статистика:\n"
            f"  👁 Просмотры: {video['views']:,}\n"
            f"  ❤️ Лайки: {video.get('likes', 0):,}\n"
            f"  💬 Комментарии: {video.get('comments', 0):,}\n"
            f"💰 Заработано: {format_currency(video['earnings'])}\n"
            f"{status_emoji} Статус: <b>{status_text}</b>\n"
            f"📅 Подано: {created_at}\n"
        )
    
    history_text += f"\n━━━━━━━━━━━━━━━━━━\n"
    history_text += f"📄 Страница {page} из {total_pages}"
    
    keyboard = pagination_keyboard(page, total_pages, "history") if total_pages > 1 else None
    
    await message.answer(history_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("history_page_"))
async def history_pagination(callback: CallbackQuery):
    """Пагинация истории"""
    page = int(callback.data.split("_")[2])
    
    items_per_page = 5
    offset = (page - 1) * items_per_page
    
    videos = await db.get_user_videos(callback.from_user.id, limit=items_per_page, offset=offset)
    total_videos = await db.get_video_count(callback.from_user.id)
    total_pages = calculate_pages(total_videos, items_per_page)
    
    history_text = f"📜 <b>История заявок</b>\n\n"
    
    for video in videos:
        status_emoji = get_status_emoji(video['status'])
        status_text = get_status_text(video['status'])
        created_at = format_timestamp(video['created_at'])
        
        # Показываем TikTok автора вместо канала
        author_display = f"@{video['video_author']}" if video.get('video_author') else video.get('channel_name', 'TikTok')
        
        history_text += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{video['id']}</code>\n"
            f"🎵 Автор: <code>{author_display}</code>\n"
            f"🔗 Ссылка: {video['video_url'][:50]}...\n"
            f"📊 Статистика:\n"
            f"  👁 Просмотры: {video['views']:,}\n"
            f"  ❤️ Лайки: {video.get('likes', 0):,}\n"
            f"  💬 Комментарии: {video.get('comments', 0):,}\n"
            f"💰 Заработано: {format_currency(video['earnings'])}\n"
            f"{status_emoji} Статус: <b>{status_text}</b>\n"
            f"📅 Подано: {created_at}\n"
        )
    
    history_text += f"\n━━━━━━━━━━━━━━━━━━\n"
    history_text += f"📄 Страница {page} из {total_pages}"
    
    keyboard = pagination_keyboard(page, total_pages, "history")
    
    await callback.message.edit_text(history_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("get_payout_"))
async def process_auto_payout(callback: CallbackQuery):
    """Автоматическая выплата для GOLD пользователей"""
    video_id = int(callback.data.split("_")[2])
    
    # Получаем данные видео
    video = await db.get_video(video_id)
    if not video:
        await callback.answer("❌ Видео не найдено", show_alert=True)
        return
    
    # Проверяем владельца
    if video['user_id'] != callback.from_user.id:
        await callback.answer("❌ Это не ваше видео!", show_alert=True)
        return
    
    # Проверяем статус пользователя
    user = await db.get_user(callback.from_user.id)
    if not user or user.get('tier') != 'gold':
        await callback.answer("❌ Доступно только для GOLD статуса!", show_alert=True)
        return
    
    # Проверяем статус видео
    if video['status'] != 'approved':
        await callback.answer("❌ Видео еще не одобрено!", show_alert=True)
        return
    
    # Проверяем, не была ли уже выплата
    if video['earnings'] <= 0:
        await callback.answer("❌ Нет средств для выплаты!", show_alert=True)
        return
    
    # Получаем способ оплаты (Crypto Pay)
    from core.crypto_pay import crypto_pay_manager
    
    try:
        # Конвертируем рубли в USDT (примерный курс 1 USDT = 95 RUB)
        usdt_amount = video['earnings'] / 95.0
        
        # Минимальная выплата 0.1 USDT
        if usdt_amount < 0.1:
            await callback.answer(f"❌ Минимальная выплата 0.1 USDT (≈9.5₽). У вас: {usdt_amount:.4f} USDT", show_alert=True)
            return
        
        # Создаем выплату через Crypto Bot
        payout_result = await crypto_pay_manager.create_payout(
            user_id=callback.from_user.id,
            amount=usdt_amount
        )
        
        if payout_result['success']:
            # Обнуляем earnings для видео
            await db.update_video_earnings(video_id, 0)
            
            # Обновляем статистику пользователя
            await db.add_to_withdrawn(callback.from_user.id, video['earnings'])
            
            # Удаляем кнопку и обновляем сообщение
            await callback.message.edit_text(
                f"{callback.message.text}\n\n"
                f"✅ <b>Выплата обработана!</b>\n"
                f"💰 Сумма: {video['earnings']:.2f} ₽ ({usdt_amount:.4f} USDT)\n"
                f"📱 Средства отправлены в Crypto Bot (@CryptoBot)",
                parse_mode="HTML"
            )
            
            # Уведомляем админов
            from core.utils import send_to_admin_chat
            await send_to_admin_chat(
                callback.bot,
                f"💰 <b>Автовыплата GOLD</b>\n\n"
                f"👤 {callback.from_user.full_name} (@{callback.from_user.username})\n"
                f"🆔 Video ID: <code>{video_id}</code>\n"
                f"💰 Сумма: {video['earnings']:.2f} ₽ ({usdt_amount:.4f} USDT)\n"
                f"✅ Выплата выполнена через Crypto Bot"
            )
            
            await callback.answer("✅ Выплата отправлена!", show_alert=True)
        else:
            await callback.answer(f"❌ Ошибка выплаты: {payout_result.get('error', 'Неизвестная ошибка')}", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка автовыплаты: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)
