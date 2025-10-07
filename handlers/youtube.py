from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import hashlib
import secrets
from datetime import datetime

from core.database import Database
from core.keyboards import cancel_keyboard, tiktok_verification_keyboard
from parsers.youtube_parser import (
    validate_youtube_url, 
    parse_youtube_channel,
    normalize_youtube_url
)
from core import config

router = Router()
db = Database(config.DATABASE_PATH)


class YouTubeStates(StatesGroup):
    waiting_for_url = State()


def generate_verification_code(user_id: int) -> str:
    """Генерация уникального кода верификации для YouTube (уникален для каждого пользователя)"""
    # Используем user_id, текущее время и секретный токен бота для максимальной уникальности
    timestamp = datetime.now().isoformat()
    random_salt = secrets.token_hex(8)  # 16 символов случайности
    
    seed = f"youtube_{user_id}_{timestamp}_{config.BOT_TOKEN}_{random_salt}"
    hash_obj = hashlib.sha256(seed.encode())
    code = hash_obj.hexdigest()[:16].upper()  # Увеличиваем до 16 символов
    
    return f"YT-{code}"


def create_progress_bar(percent: int) -> str:
    """Создает прогресс-бар визуально"""
    filled = int(percent / 10)
    empty = 10 - filled
    return f"{'🟩' * filled}{'⬜' * empty} {percent}%"


@router.callback_query(F.data == "add_youtube")
async def start_youtube_verification(callback: CallbackQuery, state: FSMContext):
    """Начать процесс привязки YouTube канала"""
    # Проверяем, нет ли уже привязанного YouTube
    youtube = await db.get_user_youtube(callback.from_user.id)
    if youtube:
        verified_status = "✅ Верифицирован" if youtube['is_verified'] else "⏳ Ожидает верификации"
        await callback.answer(
            f"У вас уже привязан YouTube канал: {youtube['channel_name']}\n{verified_status}",
            show_alert=True
        )
        return
    
    # Генерируем код верификации
    verification_code = generate_verification_code(callback.from_user.id)
    await state.update_data(verification_code=verification_code)
    
    await callback.message.edit_text(
        f"📺 <b>Привязка YouTube канала</b>\n\n"
        f"Отправьте ссылку на ваш YouTube канал:\n\n"
        f"Например: <code>https://www.youtube.com/@channelname</code>\n"
        f"или просто: <code>@channelname</code>\n\n"
        f"⚠️ <b>Важно:</b> Один YouTube канал можно привязать только к одному аккаунту!",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(YouTubeStates.waiting_for_url)
    await callback.answer()


@router.message(YouTubeStates.waiting_for_url)
async def receive_youtube_url(message: Message, state: FSMContext):
    """Получить ссылку на YouTube канал - СРАЗУ показываем код"""
    url = message.text.strip()
    
    # Валидация URL
    if not validate_youtube_url(url):
        await message.answer(
            "❌ Неверный формат ссылки!\n\n"
            "Примеры правильных ссылок:\n"
            "• <code>https://www.youtube.com/@channelname</code>\n"
            "• <code>@channelname</code>\n"
            "• <code>https://www.youtube.com/channel/UC...</code>\n\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Нормализуем URL
    normalized_url = normalize_youtube_url(url) if not url.startswith('http') else url
    
    # Получаем код верификации
    data = await state.get_data()
    verification_code = data.get('verification_code')
    
    # Сразу показываем инструкцию (без парсинга!)
    await message.answer(
        f"📺 <b>YouTube канал получен!</b>\n\n"
        f"📋 <b>Ваш код верификации:</b>\n"
        f"<code>{verification_code}</code>\n\n"
        f"<b>Инструкция:</b>\n"
        f"1️⃣ Откройте YouTube Studio\n"
        f"2️⃣ Перейдите в Настройки → Канал → Основная информация\n"
        f"3️⃣ Добавьте код в описание канала\n"
        f"4️⃣ Сохраните изменения\n"
        f"5️⃣ Нажмите кнопку \"Сменил описание\"\n\n"
        f"⏰ <b>Важно:</b> После сохранения подождите 20-30 секунд",
        reply_markup=tiktok_verification_keyboard(),
        parse_mode="HTML"
    )
    
    # Сохраняем URL для проверки после нажатия кнопки
    await state.update_data(youtube_url=normalized_url)


@router.callback_query(F.data == "tiktok_confirm_bio", YouTubeStates.waiting_for_url)
async def youtube_check_description(callback: CallbackQuery, state: FSMContext):
    """Проверка описания YouTube канала ПОСЛЕ нажатия кнопки (с парсингом)"""
    data = await state.get_data()
    verification_code = data.get('verification_code')
    youtube_url = data.get('youtube_url')
    
    if not youtube_url or not verification_code:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        await state.clear()
        return
    
    progress_msg = callback.message
    
    try:
        # Анимация ожидания (20 секунд)
        for i in range(1, 21):
            percent = int((i / 20) * 50)
            await progress_msg.edit_text(
                f"🔍 <b>Проверка канала</b>\n\n"
                f"{create_progress_bar(percent)}\n\n"
                f"⏳ Ожидание обновления... ({i}/20 сек)",
                parse_mode="HTML"
            )
            await asyncio.sleep(1)
        
        # Парсим канал
        await progress_msg.edit_text(
            f"🔍 <b>Проверка канала</b>\n\n"
            f"{create_progress_bar(60)}\n\n"
            f"📥 Загрузка данных канала...",
            parse_mode="HTML"
        )
        
        try:
            channel_data = await parse_youtube_channel(youtube_url)
        except Exception as e:
            logger.error(f"Ошибка парсинга YouTube канала: {e}")
            await progress_msg.edit_text(
                f"❌ <b>Ошибка загрузки</b>\n\n"
                f"Не удалось загрузить данные канала.\n"
                f"Возможные причины:\n"
                f"• YouTube временно недоступен\n"
                f"• Канал приватный или удален\n"
                f"• Проблемы с сетью\n\n"
                f"Попробуйте еще раз через минуту:",
                reply_markup=tiktok_verification_keyboard(),
                parse_mode="HTML"
            )
            return
        
        if not channel_data:
            await progress_msg.edit_text(
                f"❌ <b>Ошибка загрузки</b>\n\n"
                f"Не удалось загрузить данные канала.\n"
                f"Возможные причины:\n"
                f"• Неверная ссылка на канал\n"
                f"• Канал удален или приватный\n"
                f"• Таймаут загрузки (>60 сек)\n\n"
                f"Попробуйте еще раз через минуту:",
                reply_markup=tiktok_verification_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Проверяем код в описании
        await progress_msg.edit_text(
            f"🔍 <b>Проверка канала</b>\n\n"
            f"{create_progress_bar(80)}\n\n"
            f"🔍 Проверка описания...",
            parse_mode="HTML"
        )
        
        description = channel_data.get('description', '')
        
        if verification_code not in description:
            await progress_msg.edit_text(
                f"❌ <b>Код не найден</b>\n\n"
                f"📋 Ваш код: <code>{verification_code}</code>\n\n"
                f"Убедитесь, что:\n"
                f"• Код добавлен в описание канала\n"
                f"• Изменения сохранены в YouTube Studio\n"
                f"• Прошло 20-30 секунд после сохранения\n\n"
                f"Попробуйте еще раз:",
                reply_markup=tiktok_verification_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Код найден! Сохраняем
        await progress_msg.edit_text(
            f"🔍 <b>Проверка канала</b>\n\n"
            f"{create_progress_bar(100)}\n\n"
            f"✅ Код найден! Сохранение...",
            parse_mode="HTML"
        )
        
        result = await db.add_youtube_channel(
            user_id=callback.from_user.id,
            channel_id=channel_data.get('channel_id', 'UNKNOWN'),
            channel_handle=channel_data.get('channel_handle', ''),
            channel_name=channel_data.get('channel_name', 'YouTube Channel'),
            url=youtube_url,
            verification_code=verification_code
        )
        
        if not result['success']:
            error_messages = {
                'channel_already_bound': "❌ Этот канал уже привязан к другому пользователю!",
                'user_already_has_youtube': "❌ У вас уже привязан YouTube канал!",
                'database_error': "❌ Ошибка базы данных."
            }
            
            error_text = error_messages.get(result['error'], "❌ Неизвестная ошибка")
            await progress_msg.edit_text(error_text, parse_mode="HTML")
            await state.clear()
            return
        
        # Верифицируем
        await db.verify_youtube_channel(callback.from_user.id)
        
        # Успех!
        subscriber_text = channel_data.get('subscriber_text', 'N/A')
        await progress_msg.edit_text(
            f"✅ <b>YouTube канал привязан!</b>\n\n"
            f"📺 <b>Канал:</b> {channel_data.get('channel_name')}\n"
            f"👥 <b>Подписчиков:</b> {subscriber_text}\n"
            f"🆔 <b>ID:</b> <code>{channel_data.get('channel_id', 'N/A')}</code>\n\n"
            f"Теперь вы можете загружать видео!",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        await progress_msg.edit_text(
            f"❌ <b>Ошибка:</b> {str(e)}\n\n"
            f"Попробуйте позже.",
            parse_mode="HTML"
        )
        await state.clear()
    
    await callback.answer()
