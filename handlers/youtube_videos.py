from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime

from database import Database
from keyboards import cancel_keyboard
from youtube_video_parser import (
    validate_youtube_video_url,
    parse_youtube_video,
    extract_video_id,
    is_video_fresh
)
import config

logger = logging.getLogger(__name__)

router = Router()
db = Database(config.DATABASE_PATH)


class YouTubeVideoStates(StatesGroup):
    waiting_for_video_url = State()


def create_progress_bar(percent: int) -> str:
    """Создает прогресс-бар визуально"""
    filled = int(percent / 10)
    empty = 10 - filled
    return f"{'🟩' * filled}{'⬜' * empty} {percent}%"


@router.callback_query(F.data == "submit_youtube_video")
async def start_youtube_video_submission(callback: CallbackQuery, state: FSMContext):
    """Начать процесс подачи YouTube видео"""
    user_id = callback.from_user.id
    
    # Проверяем, есть ли привязанный YouTube канал
    youtube = await db.get_user_youtube(user_id)
    
    if not youtube:
        await callback.answer(
            "❌ Сначала привяжите YouTube канал в профиле!",
            show_alert=True
        )
        return
    
    if not youtube['is_verified']:
        await callback.answer(
            "❌ Ваш YouTube канал еще не верифицирован!",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        f"📺 <b>Подача YouTube видео</b>\n\n"
        f"🎬 <b>Ваш канал:</b> {youtube['channel_name']}\n"
        f"🆔 <b>Channel ID:</b> <code>{youtube['channel_id']}</code>\n\n"
        f"📤 <b>Отправьте ссылку на видео</b>\n\n"
        f"Примеры:\n"
        f"• <code>https://www.youtube.com/watch?v=...</code>\n"
        f"• <code>https://youtu.be/...</code>\n"
        f"• <code>https://www.youtube.com/shorts/...</code>\n\n"
        f"⚠️ <b>Важно:</b>\n"
        f"• Видео должно быть с вашего канала\n"
        f"• Видео должно быть загружено не позднее 24 часов назад\n"
        f"• Видео не должно было подаваться ранее",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(YouTubeVideoStates.waiting_for_video_url)
    await state.update_data(youtube_channel_id=youtube['id'], youtube_channel_handle=youtube['channel_id'])
    await callback.answer()


@router.message(YouTubeVideoStates.waiting_for_video_url)
async def receive_youtube_video_url(message: Message, state: FSMContext):
    """Получить ссылку на YouTube видео и проверить его"""
    url = message.text.strip()
    
    # Валидация URL
    if not validate_youtube_video_url(url):
        await message.answer(
            "❌ Неверный формат ссылки!\n\n"
            "Примеры правильных ссылок:\n"
            "• <code>https://www.youtube.com/watch?v=dQw4w9WgXcQ</code>\n"
            "• <code>https://youtu.be/dQw4w9WgXcQ</code>\n"
            "• <code>https://www.youtube.com/shorts/abc123</code>\n\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Проверяем, не подавалось ли это видео ранее
    video_exists = await db.check_youtube_video_exists(video_url=url)
    if video_exists:
        await message.answer(
            "❌ <b>Это видео уже было подано ранее!</b>\n\n"
            "Каждое видео можно подать только один раз.",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Прогресс сообщение
    progress_msg = await message.answer(
        f"🔍 <b>Проверка видео</b>\n\n"
        f"{create_progress_bar(10)}\n\n"
        f"⏳ Загрузка данных видео...",
        parse_mode="HTML"
    )
    
    # Парсим видео
    video_data = await parse_youtube_video(url)
    
    if not video_data:
        await progress_msg.edit_text(
            "❌ <b>Ошибка загрузки</b>\n\n"
            "Не удалось получить данные видео.\n"
            "Возможные причины:\n"
            "• Видео удалено или недоступно\n"
            "• Видео приватное\n"
            "• Временные проблемы с YouTube\n\n"
            "Попробуйте еще раз позже:",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Обновляем прогресс
    await progress_msg.edit_text(
        f"🔍 <b>Проверка видео</b>\n\n"
        f"{create_progress_bar(40)}\n\n"
        f"✅ Видео найдено: {video_data['title']}\n"
        f"⏳ Проверка канала...",
        parse_mode="HTML"
    )
    
    # Проверяем лимит 1 видео в 24 часа
    can_submit, time_remaining = await db.can_submit_youtube_video(message.from_user.id)
    if not can_submit:
        await progress_msg.edit_text(
            f"⏰ <b>Превышен лимит отправки видео!</b>\n\n"
            f"Вы можете отправлять максимум 1 YouTube видео в 24 часа.\n\n"
            f"⏳ <b>До следующей отправки:</b> {time_remaining}\n\n"
            f"Попробуйте позже!",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Получаем данные о привязанном канале
    data = await state.get_data()
    user_youtube_channel_id = data.get('youtube_channel_handle')
    
    # Проверяем, что видео с привязанного канала
    if video_data['channel_id'] != user_youtube_channel_id:
        await progress_msg.edit_text(
            f"❌ <b>Видео не с вашего канала!</b>\n\n"
            f"📺 <b>Канал видео:</b> {video_data['channel_name']}\n"
            f"🆔 <b>ID канала:</b> <code>{video_data['channel_id']}</code>\n\n"
            f"🔗 <b>Ваш привязанный канал:</b> <code>{user_youtube_channel_id}</code>\n\n"
            f"Вы можете подавать только видео со своего привязанного канала!",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Обновляем прогресс
    await progress_msg.edit_text(
        f"🔍 <b>Проверка видео</b>\n\n"
        f"{create_progress_bar(70)}\n\n"
        f"✅ Канал подтвержден\n"
        f"⏳ Проверка даты публикации...",
        parse_mode="HTML"
    )
    
    # Проверяем, что видео свежее (не старше 24 часов)
    if not is_video_fresh(video_data['upload_date'], hours=24):
        upload_date_str = video_data['upload_date'].strftime('%d.%m.%Y %H:%M') if video_data['upload_date'] else 'Неизвестно'
        await progress_msg.edit_text(
            f"❌ <b>Видео слишком старое!</b>\n\n"
            f"📅 <b>Дата загрузки:</b> {upload_date_str}\n\n"
            f"Вы можете подавать только видео, загруженные не позднее 24 часов назад.\n\n"
            f"⏰ Попробуйте подать более свежее видео!",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Обновляем прогресс
    await progress_msg.edit_text(
        f"🔍 <b>Проверка видео</b>\n\n"
        f"{create_progress_bar(90)}\n\n"
        f"✅ Дата публикации подходит\n"
        f"⏳ Сохранение видео...",
        parse_mode="HTML"
    )
    
    # Сохраняем видео в базу
    youtube_db_id = data.get('youtube_channel_id')
    video_id = await db.add_youtube_video(
        user_id=message.from_user.id,
        youtube_channel_id=youtube_db_id,
        video_url=url,
        video_id=video_data['video_id'],
        title=video_data['title'],
        author=video_data['channel_name'],
        published_at=video_data['upload_date_str'],
        views=video_data['view_count'],
        likes=video_data['like_count'],
        comments=video_data['comment_count']
    )
    
    if not video_id:
        await progress_msg.edit_text(
            "❌ <b>Ошибка сохранения</b>\n\n"
            "Не удалось сохранить видео в базу данных.\n"
            "Возможно, оно уже было добавлено ранее.",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Успех!
    await progress_msg.edit_text(
        f"✅ <b>Видео успешно подано!</b>\n\n"
        f"🎬 <b>Название:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
        f"📺 <b>Канал:</b> {video_data['channel_name']}\n"
        f"📅 <b>Загружено:</b> {video_data['upload_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📊 <b>Статистика на момент подачи:</b>\n"
        f"👁 Просмотры: {video_data['view_count']:,}\n"
        f"👍 Лайки: {video_data['like_count']:,}\n"
        f"💬 Комментарии: {video_data['comment_count']:,}\n\n"
        f"⏳ <b>Статус:</b> Ожидает проверки\n\n"
        f"Видео будет проверено администратором в ближайшее время.",
        parse_mode="HTML"
    )
    
    await state.clear()
    
    # Уведомляем администратора в админ-чат
    try:
        from utils import send_to_admin_chat
        from keyboards import video_moderation_keyboard, first_youtube_video_keyboard
        
        user = await db.get_user(message.from_user.id)
        
        # Проверяем уровень пользователя и наличие ставки
        user_tier = await db.get_user_tier(message.from_user.id)
        user_rate = await db.get_user_youtube_rate(message.from_user.id)
        
        # Если пользователь Gold и у него уже есть ставка - автоматическая выплата
        if user_tier == 'gold' and user_rate and user_rate > 0:
            # Автоматически одобряем видео и устанавливаем выплату
            await db.update_video_status(video_id, 'approved')
            await db.update_video_earnings(video_id, user_rate)
            
            # Автоматически выплачиваем
            from crypto_pay import send_payment, calculate_usdt_amount
            
            # Отправляем платеж
            payment_result = await send_payment(
                user_id=message.from_user.id,
                amount_rub=user_rate,
                spend_id=f"youtube_auto_{video_id}"
            )
            
            if payment_result['success']:
                # Обновляем сообщение пользователю
                await progress_msg.edit_text(
                    f"🎉 <b>Видео автоматически одобрено и оплачено!</b>\n\n"
                    f"🥇 <b>Ваш статус:</b> GOLD\n\n"
                    f"🎬 <b>Название:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
                    f"📺 <b>Канал:</b> {video_data['channel_name']}\n"
                    f"📅 <b>Загружено:</b> {video_data['upload_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"💰 <b>Выплата:</b> {user_rate:.2f}₽\n"
                    f"💵 <b>В USDT:</b> {payment_result['usdt_amount']:.2f}\n\n"
                    f"💳 <b>Выплата через @CryptoBot</b>\n"
                    f"✅ Средства отправлены на ваш @CryptoBot кошелек!\n\n"
                    f"ℹ️ <i>Для получения средств нужен аккаунт в @CryptoBot.\n"
                    f"Если у вас еще нет аккаунта - просто напишите /start боту @CryptoBot</i>",
                    parse_mode="HTML"
                )
                
                # Уведомляем админ-чат
                admin_text = (
                    f"✅ <b>YouTube видео автоматически оплачено</b> (GOLD)\n\n"
                    f"👤 <b>Пользователь:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
                    f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
                    f"🥇 <b>Статус:</b> GOLD\n\n"
                    f"🎬 <b>Видео:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
                    f"📺 <b>Канал:</b> {video_data['channel_name']}\n"
                    f"🔗 <b>Ссылка:</b> {url}\n\n"
                    f"📊 <b>Статистика:</b>\n"
                    f"👁 Просмотры: {video_data['view_count']:,}\n"
                    f"👍 Лайки: {video_data['like_count']:,}\n"
                    f"💬 Комментарии: {video_data['comment_count']:,}\n\n"
                    f"💰 <b>Выплата:</b> {user_rate:.2f}₽\n"
                    f"💵 <b>В USDT:</b> {payment_result['usdt_amount']:.2f}\n"
                    f"✅ <b>Transfer ID:</b> {payment_result['transfer'].transfer_id if payment_result.get('transfer') else 'N/A'}"
                )
                await send_to_admin_chat(message.bot, admin_text)
                return
            else:
                # Ошибка платежа - уведомляем пользователя
                await progress_msg.edit_text(
                    f"⚠️ <b>Видео одобрено, но ошибка выплаты</b>\n\n"
                    f"🎬 <b>Видео:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n\n"
                    f"💰 <b>Сумма:</b> {user_rate:.2f}₽\n\n"
                    f"❌ <b>Ошибка:</b> {payment_result['error']}\n\n"
                    f"Обратитесь к администратору.",
                    parse_mode="HTML"
                )
                
                # Уведомляем админ-чат об ошибке
                admin_text = (
                    f"⚠️ <b>Ошибка автоматической выплаты!</b>\n\n"
                    f"👤 <b>Пользователь:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
                    f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
                    f"🥇 <b>Статус:</b> GOLD\n\n"
                    f"🎬 <b>Видео:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
                    f"🔗 <b>Ссылка:</b> {url}\n\n"
                    f"💰 <b>Сумма:</b> {user_rate:.2f}₽\n\n"
                    f"❌ <b>Ошибка Crypto Bot:</b>\n{payment_result['error']}"
                )
                await send_to_admin_chat(message.bot, admin_text)
                return
        
        # Если не Gold или нет ставки - стандартная проверка админом
        is_first_video = await db.check_first_youtube_video(message.from_user.id)
        
        # Проверяем, было ли уже одобрено хоть одно видео
        video_with_earnings = await db.get_video_with_details(video_id)
        has_previous_approved = video_with_earnings and video_with_earnings.get('earnings', 0) > 0
        
        if is_first_video or not has_previous_approved:
            # Первое видео - админ должен установить выплату
            admin_text = (
                f"🆕 <b>ПЕРВОЕ YouTube видео на проверку</b> ⭐️\n\n"
                f"👤 <b>Пользователь:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
                f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n\n"
                f"🎬 <b>Видео:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
                f"📺 <b>Канал:</b> {video_data['channel_name']}\n"
                f"🔗 <b>Ссылка:</b> {url}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"👁 Просмотры: {video_data['view_count']:,}\n"
                f"👍 Лайки: {video_data['like_count']:,}\n"
                f"💬 Комментарии: {video_data['comment_count']:,}\n\n"
                f"💰 <b>Выплата не установлена!</b>\n"
                f"Нажми 'Установить выплату' чтобы задать сумму за это видео."
            )
            keyboard = first_youtube_video_keyboard(video_id)
        else:
            # Обычное видео
            admin_text = (
                f"🆕 <b>Новое YouTube видео на проверку</b>\n\n"
                f"👤 <b>Пользователь:</b> {user['full_name']} (@{user['username'] or 'нет'})\n"
                f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n\n"
                f"🎬 <b>Видео:</b> {video_data['title'][:50]}{'...' if len(video_data['title']) > 50 else ''}\n"
                f"📺 <b>Канал:</b> {video_data['channel_name']}\n"
                f"🔗 <b>Ссылка:</b> {url}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"👁 Просмотры: {video_data['view_count']:,}\n"
                f"👍 Лайки: {video_data['like_count']:,}\n"
                f"💬 Комментарии: {video_data['comment_count']:,}"
            )
            keyboard = video_moderation_keyboard(video_id)
        
        await send_to_admin_chat(
            message.bot,
            admin_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления в админ-чат: {e}")


@router.callback_query(F.data == "cancel")
async def cancel_video_submission(callback: CallbackQuery, state: FSMContext):
    """Отменить подачу видео"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Подача видео отменена.",
        parse_mode="HTML"
    )
    await callback.answer()
