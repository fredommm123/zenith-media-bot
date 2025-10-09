"""
Обработчики для системы автоматических выплат через Crypto Pay
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.database import Database
from core.crypto_pay import send_payment, calculate_usdt_amount
from core import config
from core.keyboards import admin_payout_keyboard
from core.utils import send_to_admin_chat

logger = logging.getLogger(__name__)

router = Router()
db = Database(config.DATABASE_PATH)


async def calculate_payout_amount(views: int, platform: str, user_id: int = None, video_id: int = None) -> float:
    """
    Рассчитать сумму выплаты
    
    Args:
        views: Количество просмотров (для TikTok)
        platform: Платформа ('tiktok' или 'youtube')
        user_id: ID пользователя
        video_id: ID видео (для YouTube фиксированной ставки)
        
    Returns:
        float: Сумма в рублях
    """
    if platform == 'tiktok':
        # TikTok: фиксированная ставка 65₽ за 1000 просмотров
        rate = config.TIKTOK_RATE_PER_1000_VIEWS
        amount = (views / 1000) * rate
        
    elif platform == 'youtube':
        # YouTube: индивидуальная ставка, устанавливается админом
        if video_id:
            # Получаем сохраненную сумму для видео
            video = await db.get_video(video_id)
            if video and video.get('earnings', 0) > 0:
                amount = video['earnings']
            else:
                # Если ставка не установлена админом - возвращаем 0
                amount = 0
        else:
            # Без video_id не можем определить ставку
            amount = 0
    else:
        amount = 0
    
    return round(amount, 2)


async def format_payout_notification(
    video_data: dict,
    user_id: int,
    username: str,
    full_name: str,
    payout_amount: float,
    usdt_amount: float
) -> str:
    """Сформировать текст уведомления о выплате для админов"""
    
    platform_emoji = "🎵" if video_data['platform'] == 'tiktok' else "📺"
    platform_name = "TikTok" if video_data['platform'] == 'tiktok' else "YouTube"
    
    # Получаем информацию о канале
    channel_info = video_data.get('channel_info', {})
    
    # Получаем уровень пользователя
    user_tier = await db.get_user_tier(user_id)
    tier_emoji = "🥉" if user_tier == "bronze" else "🥇"
    tier_desc = "после одобрения админом" if user_tier == "bronze" else "автоматически"
    
    if video_data['platform'] == 'tiktok':
        channel_display = f"@{channel_info.get('username', 'неизвестен')}"
    else:
        channel_display = channel_info.get('channel_name', 'Неизвестен')
        rate = channel_info.get('rate_per_1000_views', 0)  # Для YouTube админ должен установить ставку
    
    text = (
        f"💰 <b>Запрос на выплату</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Пользователь:</b>\n"
        f"  • Имя: {full_name}\n"
        f"  • Username: @{username}\n"
        f"  • ID: <code>{user_id}</code>\n"
        f"  • {tier_emoji} Уровень: <b>{user_tier.upper()}</b> ({tier_desc})\n\n"
        f"{platform_emoji} <b>Платформа:</b> {platform_name}\n"
        f"📺 <b>Канал:</b> {channel_display}\n"
    )
    
    if video_data['platform'] == 'youtube':
        text += f"📊 <b>Ставка:</b> {rate} ₽ за 1K просмотров\n"
    
    text += (
        f"\n🎬 <b>Информация о видео:</b>\n"
        f"  • ID: <code>{video_data['id']}</code>\n"
    )
    
    if video_data.get('video_title'):
        title = video_data['video_title']
        if len(title) > 60:
            title = title[:60] + "..."
        text += f"  • Название: {title}\n"
    
    text += (
        f"  • URL: {video_data['video_url']}\n\n"
        f"📈 <b>Статистика видео:</b>\n"
        f"  • 👁 Просмотры: {video_data['views']:,}\n"
        f"  • ❤️ Лайки: {video_data.get('likes', 0):,}\n"
        f"  • 💬 Комментарии: {video_data.get('comments', 0):,}\n"
    )
    
    if video_data.get('shares'):
        text += f"  • 🔄 Репосты: {video_data['shares']:,}\n"
    
    text += f"\n💸 <b>Расчет выплаты:</b>\n"
    
    if video_data['platform'] == 'tiktok':
        text += (
            f"  • Просмотров: {video_data['views']:,}\n"
            f"  • Ставка: {config.TIKTOK_RATE_PER_1000_VIEWS} ₽ / 1000 👁\n"
            f"  • Формула: {video_data['views']:,} / 1000 × {config.TIKTOK_RATE_PER_1000_VIEWS}\n"
        )
    else:  # youtube
        text += f"  • 💵 Фиксированная выплата за видео\n"
    
    text += (
        f"  • <b>Сумма: {payout_amount:.2f} ₽</b>\n"
        f"  • <b>В USDT: ~{usdt_amount:.6f} USDT</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⬇️ Выберите действие:"
    )
    
    return text


@router.callback_query(F.data.startswith("request_payout_"))
async def request_payout_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка запроса на выплату по видео"""
    
    video_id = int(callback.data.split("_")[2])
    
    # Получаем полную информацию о видео
    video = await db.get_video_with_details(video_id)
    
    if not video:
        await callback.answer("❌ Видео не найдено!", show_alert=True)
        return
    
    # Проверяем, что это видео пользователя
    if video['user_id'] != callback.from_user.id:
        await callback.answer("❌ Это не ваше видео!", show_alert=True)
        return
    
    # Проверяем статус видео
    if video['status'] != 'approved':
        await callback.answer(
            "❌ Выплата доступна только для одобренных видео!",
            show_alert=True
        )
        return
    
    # Рассчитываем сумму выплаты
    views = video['views']
    platform = video['platform']
    user_id = video['user_id']
    
    payout_amount = await calculate_payout_amount(views, platform, user_id, video_id)
    
    # Конвертируем в USDT
    usdt_amount = await calculate_usdt_amount(payout_amount)
    
    if usdt_amount is None:
        await callback.answer(
            "❌ Ошибка получения курса валют. Попробуйте позже.",
            show_alert=True
        )
        return
    
    # Проверка минимума 1 USDT
    if usdt_amount < 1.0:
        await callback.answer(
            f"❌ Минимальная сумма для вывода: 1 USDT\n"
            f"Ваша сумма: {usdt_amount:.4f} USDT ({payout_amount:.2f} ₽)",
            show_alert=True
        )
        return
    
    # Получаем tier пользователя
    user = await db.get_user(user_id)
    tier = user.get('tier', 'bronze') if user else 'bronze'
    username = user.get('username') if user else callback.from_user.username
    
    # Если нет username, используем user_id
    if not username:
        username = f"user_{user_id}"
    
    # === BRONZE: Отправляем запрос админу ===
    if tier == 'bronze':
        await callback.message.edit_text(
            f"📤 <b>Запрос на выплату отправлен!</b>\n\n"
            f"🥉 <b>Ваш статус:</b> BRONZE\n"
            f"💰 <b>Сумма:</b> {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n"
            f"📊 <b>Видео ID:</b> {video_id}\n\n"
            f"⏳ Ожидайте одобрения администратора.\n"
            f"Это может занять некоторое время.",
            parse_mode="HTML"
        )
        
        # Отправляем уведомление админу
        from core.keyboards import InlineKeyboardMarkup, InlineKeyboardButton
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выплатить", callback_data=f"admin_payout_{video_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_payout_{video_id}")
            ]
        ])
        
        from core.utils import send_to_admin_chat
        await send_to_admin_chat(
            f"💰 <b>Запрос на выплату (BRONZE)</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Пользователь:</b>\n"
            f"  • Имя: {user.get('full_name', 'Неизвестно')}\n"
            f"  • Username: @{username}\n"
            f"  • ID: {user_id}\n"
            f"  • 🥉 Уровень: BRONZE\n\n"
            f"🎬 <b>Видео:</b>\n"
            f"  • ID: {video_id}\n"
            f"  • URL: {video['video_url']}\n"
            f"  • Платформа: {platform.upper()}\n"
            f"  • Просмотры: {views:,}\n\n"
            f"💸 <b>Выплата:</b>\n"
            f"  • Сумма: {payout_amount:.2f} ₽\n"
            f"  • В USDT: ~{usdt_amount:.4f} USDT\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⬇️ Выберите действие:",
            keyboard=admin_keyboard
        )
        
        await callback.answer("✅ Запрос отправлен админу!")
        return
    
    # === GOLD: Автоматическая выплата ===
    # Генерируем уникальный spend_id для идемпотентности
    spend_id = f"video_{video_id}_{datetime.now().timestamp()}"
    
    # Отправляем выплату напрямую через Crypto Bot
    await callback.message.edit_text(
        f"⏳ <b>Отправка выплаты...</b>\n\n"
        f"🥇 <b>Ваш статус:</b> GOLD (автоматическая выплата)\n"
        f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n"
        f"📊 Видео ID: <code>{video_id}</code>",
        parse_mode="HTML"
    )
    
    # Отправляем платеж
    payment_result = await send_payment(
        user_id=user_id,
        username=username,
        amount_usdt=usdt_amount,
        spend_id=spend_id,
        comment=f"Выплата за видео #{video_id}"
    )
    
    if payment_result['success']:
        # Обновляем статус видео
        await db.update_video_status(video_id, "paid_out")
        await db.update_video_earnings(video_id, payout_amount)
        
        # Обновляем статистику пользователя
        await db.update_user_stats_withdrawal(user_id, payout_amount)
        
        # Успешная выплата
        await callback.message.edit_text(
            f"✅ <b>Выплата успешно отправлена!</b>\n\n"
            f"💰 Сумма: <b>{payout_amount:.2f} ₽</b>\n"
            f"💵 В USDT: <b>{usdt_amount:.6f} USDT</b>\n\n"
            f"📊 Видео ID: <code>{video_id}</code>\n"
            f"👁 Просмотров: {views:,}\n\n"
            f"🎉 Деньги отправлены на ваш @CryptoBot аккаунт!\n"
            f"Проверьте @CryptoBot - деньги уже там.",
            parse_mode="HTML"
        )
        
        # Уведомляем админов
        await send_to_admin_chat(
            callback.bot,
            f"✅ <b>Автоматическая выплата выполнена</b>\n\n"
            f"👤 Пользователь: {callback.from_user.full_name} (@{username})\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"📊 Video ID: <code>{video_id}</code>\n\n"
            f"💰 Сумма: {payout_amount:.2f} ₽ ({usdt_amount:.6f} USDT)\n"
            f"🔗 {video['video_url']}",
            parse_mode="HTML"
        )
    else:
        # Ошибка выплаты
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        
        await callback.message.edit_text(
            f"❌ <b>Ошибка выплаты!</b>\n\n"
            f"{error_msg}\n\n"
            f"Попробуйте позже или обратитесь к администратору.",
            parse_mode="HTML"
        )
        
        # Уведомляем админов об ошибке
        await send_to_admin_chat(
            callback.bot,
            f"⚠️ <b>Ошибка автоматической выплаты</b>\n\n"
            f"👤 Пользователь: {callback.from_user.full_name} (@{username})\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"📊 Video ID: <code>{video_id}</code>\n\n"
            f"💰 Сумма: {payout_amount:.2f} ₽ ({usdt_amount:.6f} USDT)\n"
            f"❌ Ошибка: {error_msg}",
            parse_mode="HTML"
        )
    
    await callback.answer()
    
    await callback.answer("✅ Запрос отправлен!")


@router.callback_query(F.data.startswith("approve_payout_"))
async def approve_payout_callback(callback: CallbackQuery):
    """Админ одобряет выплату"""
    
    # Проверяем, что это админ
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ У вас нет прав!", show_alert=True)
        return
    
    payout_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о выплате
    payout = await db.get_payout_by_id(payout_id)
    
    if not payout:
        await callback.answer("❌ Выплата не найдена!", show_alert=True)
        return
    
    if payout['status'] != 'pending':
        await callback.answer(
            f"❌ Выплата уже обработана!\nСтатус: {payout['status']}",
            show_alert=True
        )
        return
    
    # Проверяем уровень пользователя (без задержки 24ч для bronze)
    user_tier = await db.get_user_tier(payout['user_id'])
    
    # Для bronze и gold выплата происходит сразу после одобрения админом
    # Обновляем сообщение админа
    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"⏳ <b>Обработка выплаты...</b>",
        parse_mode="HTML"
    )
    
    # Отправляем USDT через Crypto Pay
    result = await send_payment(
        user_id=payout['user_id'],
        amount_rub=payout['amount_rub'],
        spend_id=payout['spend_id'],
        comment=f"Выплата за видео ID {payout['video_id']}"
    )
    
    if result['success']:
        # Обновляем статус выплаты
        await db.update_payout_status(
            payout_id=payout_id,
            status='paid',
            transfer_id=result['transfer'].transfer_id,
            admin_id=callback.from_user.id
        )
        
        # Обновляем сообщение админа
        await callback.message.edit_text(
            f"{callback.message.text.split('⏳ Обработка')[0]}\n"
            f"✅ <b>ВЫПЛАЧЕНО</b>\n\n"
            f"💰 Отправлено: {payout['amount_rub']:.2f} ₽\n"
            f"💵 В USDT: {result['usdt_amount']:.6f} USDT\n"
            f"🆔 Transfer ID: <code>{result['transfer'].transfer_id}</code>\n"
            f"👨‍💼 Админ: {callback.from_user.full_name}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )
        
        # Уведомляем пользователя
        try:
            await callback.bot.send_message(
                chat_id=payout['user_id'],
                text=(
                    f"✅ <b>Выплата успешно выполнена!</b>\n\n"
                    f"🆔 ID выплаты: <code>{payout_id}</code>\n"
                    f"💰 Сумма: <b>{payout['amount_rub']:.2f} ₽</b>\n"
                    f"💵 Получено: <b>{result['usdt_amount']:.6f} USDT</b>\n\n"
                    f"💼 Деньги отправлены на ваш @CryptoBot аккаунт.\n"
                    f"Проверьте баланс в боте!"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {payout['user_id']}: {e}")
        
        await callback.answer("✅ Выплата успешно выполнена!")
        
    else:
        # Ошибка при выплате
        await db.update_payout_status(
            payout_id=payout_id,
            status='failed',
            admin_id=callback.from_user.id
        )
        
        error_msg = result['error']
        
        await callback.message.edit_text(
            f"{callback.message.text.split('⏳ Обработка')[0]}\n"
            f"❌ <b>ОШИБКА ВЫПЛАТЫ</b>\n\n"
            f"⚠️ Причина: {error_msg}\n"
            f"👨‍💼 Админ: {callback.from_user.full_name}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML",
            reply_markup=admin_payout_keyboard(payout_id)  # Возвращаем кнопки
        )
        
        # Уведомляем пользователя об ошибке
        try:
            await callback.bot.send_message(
                chat_id=payout['user_id'],
                text=(
                    f"❌ <b>Ошибка при выплате</b>\n\n"
                    f"🆔 ID выплаты: <code>{payout_id}</code>\n"
                    f"⚠️ Причина: {error_msg}\n\n"
                    f"Обратитесь к администратору для решения проблемы."
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {payout['user_id']}: {e}")
        
        await callback.answer(f"❌ Ошибка: {error_msg}", show_alert=True)


@router.callback_query(F.data.startswith("reject_payout_"))
async def reject_payout_callback(callback: CallbackQuery):
    """Админ отклоняет выплату"""
    
    # Проверяем, что это админ
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ У вас нет прав!", show_alert=True)
        return
    
    payout_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о выплате
    payout = await db.get_payout_by_id(payout_id)
    
    if not payout:
        await callback.answer("❌ Выплата не найдена!", show_alert=True)
        return
    
    if payout['status'] != 'pending':
        await callback.answer(
            f"❌ Выплата уже обработана!\nСтатус: {payout['status']}",
            show_alert=True
        )
        return
    
    # Обновляем статус
    await db.update_payout_status(
        payout_id=payout_id,
        status='rejected',
        admin_id=callback.from_user.id
    )
    
    # Обновляем сообщение админа
    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"❌ <b>ОТКЛОНЕНО</b>\n"
        f"👨‍💼 Админ: {callback.from_user.full_name}\n"
        f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            chat_id=payout['user_id'],
            text=(
                f"❌ <b>Выплата отклонена</b>\n\n"
                f"🆔 ID выплаты: <code>{payout_id}</code>\n"
                f"💰 Сумма: {payout['amount_rub']:.2f} ₽\n\n"
                f"Для уточнения причины обратитесь к администратору."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {payout['user_id']}: {e}")
    
    await callback.answer("✅ Выплата отклонена")


@router.callback_query(F.data == "request_balance_payout")
async def request_balance_payout_callback(callback: CallbackQuery):
    """Запрос выплаты с баланса пользователя"""
    
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден!", show_alert=True)
        return
    
    balance = user['balance']
    
    if balance <= 0:
        await callback.answer(
            "❌ Ваш баланс пуст!\nЗарабатывайте, отправляя видео.",
            show_alert=True
        )
        return
    
    # Конвертируем баланс в USDT
    from core.crypto_pay import get_exchange_rate_rub_to_usdt
    rate = await get_exchange_rate_rub_to_usdt()
    
    if not rate:
        await callback.answer(
            "❌ Ошибка получения курса валют. Попробуйте позже.",
            show_alert=True
        )
        return
    
    usdt_amount = balance / rate
    
    # Проверка минимума 1 USDT
    if usdt_amount < 1.0:
        needed_rub = (1.0 - usdt_amount) * rate
        await callback.answer(
            f"❌ Минимум для вывода: 1 USDT (~{rate:.2f} ₽)\n\n"
            f"Ваш баланс: {balance:.2f} ₽ (~{usdt_amount:.4f} USDT)\n"
            f"Осталось накопить: ~{needed_rub:.2f} ₽",
            show_alert=True
        )
        return
    
    # Получаем username (если нет - используем user_id)
    username = user.get('username') or callback.from_user.username
    if not username:
        username = f"user_{user_id}"
    
    # Отправляем сообщение о начале выплаты
    await callback.message.edit_text(
        f"⏳ <b>Отправка выплаты...</b>\n\n"
        f"💰 Сумма: {balance:.2f} ₽ (~{usdt_amount:.4f} USDT)\n"
        f"💳 С баланса аккаунта",
        parse_mode="HTML"
    )
    
    # Генерируем уникальный spend_id
    spend_id = f"balance_{user_id}_{datetime.now().timestamp()}"
    
    # Отправляем платеж
    payment_result = await send_payment(
        user_id=user_id,
        username=username,
        amount_usdt=usdt_amount,
        spend_id=spend_id,
        comment=f"Выплата с баланса"
    )
    
    if payment_result['success']:
        # Обнуляем баланс пользователя
        await db.update_user_balance(user_id, 0, operation='set')
        
        # Обновляем статистику выводов
        await db.update_user_stats_withdrawal(user_id, balance)
        
        # Успешная выплата
        await callback.message.edit_text(
            f"✅ <b>Выплата успешно отправлена!</b>\n\n"
            f"💰 Сумма: <b>{balance:.2f} ₽</b>\n"
            f"💵 В USDT: <b>{usdt_amount:.6f} USDT</b>\n\n"
            f"💳 Выплачено с баланса аккаунта\n"
            f"💼 Новый баланс: <b>0.00 ₽</b>\n\n"
            f"🎉 Деньги отправлены на ваш @CryptoBot аккаунт!\n"
            f"Проверьте @CryptoBot - деньги уже там.",
            parse_mode="HTML"
        )
        
        # Уведомляем админов
        await send_to_admin_chat(
            callback.bot,
            f"✅ <b>Автоматическая выплата с баланса</b>\n\n"
            f"👤 Пользователь: {callback.from_user.full_name} (@{username})\n"
            f"🆔 User ID: <code>{user_id}</code>\n\n"
            f"💰 Сумма: {balance:.2f} ₽ ({usdt_amount:.6f} USDT)\n"
            f"💳 С баланса аккаунта",
            parse_mode="HTML"
        )
    else:
        # Ошибка выплаты
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        
        await callback.message.edit_text(
            f"❌ <b>Ошибка выплаты!</b>\n\n"
            f"{error_msg}\n\n"
            f"Ваш баланс не изменен: {balance:.2f} ₽\n"
            f"Попробуйте позже или обратитесь к администратору.",
            parse_mode="HTML"
        )
        
        # Уведомляем админов об ошибке
        await send_to_admin_chat(
            callback.bot,
            f"⚠️ <b>Ошибка выплаты с баланса</b>\n\n"
            f"👤 Пользователь: {callback.from_user.full_name} (@{username})\n"
            f"🆔 User ID: <code>{user_id}</code>\n\n"
            f"💰 Сумма: {balance:.2f} ₽ ({usdt_amount:.6f} USDT)\n"
            f"❌ Ошибка: {error_msg}",
            parse_mode="HTML"
        )
    
    await callback.answer()


# ==========================================
# АДМИНСКИЕ ОБРАБОТЧИКИ ДЛЯ BRONZE ВЫПЛАТ
# ==========================================

@router.callback_query(F.data.startswith("admin_payout_"))
async def admin_approve_payout(callback: CallbackQuery):
    """Админ одобряет выплату для Bronze пользователя"""
    from core import config
    
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    video_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о видео
    video = await db.get_video_with_details(video_id)
    
    if not video:
        await callback.answer("❌ Видео не найдено!", show_alert=True)
        return
    
    user_id = video['user_id']
    views = video['views']
    platform = video['platform']
    
    # Рассчитываем сумму
    payout_amount = await calculate_payout_amount(views, platform, user_id, video_id)
    usdt_amount = await calculate_usdt_amount(payout_amount)
    
    if not usdt_amount:
        await callback.message.edit_text(
            f"❌ <b>Ошибка!</b>\n\nНе удалось получить курс валют.",
            parse_mode="HTML"
        )
        return
    
    # Получаем данные пользователя
    user = await db.get_user(user_id)
    username = user.get('username') if user else None
    if not username:
        username = f"user_{user_id}"
    
    # Генерируем spend_id
    spend_id = f"video_{video_id}_{datetime.now().timestamp()}"
    
    # Отправляем выплату
    await callback.message.edit_text(
        f"⏳ <b>Отправка выплаты...</b>\n\n"
        f"👤 Пользователь: {user_id}\n"
        f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)",
        parse_mode="HTML"
    )
    
    payment_result = await send_payment(
        user_id=user_id,
        username=username,
        amount_usdt=usdt_amount,
        spend_id=spend_id,
        comment=f"Выплата за видео #{video_id}"
    )
    
    if payment_result['success']:
        await callback.message.edit_text(
            f"✅ <b>Выплата успешно отправлена!</b>\n\n"
            f"👤 Пользователь: {user.get('full_name', 'Неизвестно')} (@{username})\n"
            f"🆔 ID: {user_id}\n"
            f"📊 Видео ID: {video_id}\n"
            f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n\n"
            f"✅ Деньги отправлены на @CryptoBot аккаунт пользователя.",
            parse_mode="HTML"
        )
        
        # Уведомляем пользователя
        try:
            await callback.bot.send_message(
                user_id,
                f"✅ <b>Выплата одобрена!</b>\n\n"
                f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n"
                f"📊 Видео ID: {video_id}\n\n"
                f"💳 Деньги отправлены на ваш @CryptoBot аккаунт!\n"
                f"Проверьте баланс в боте.",
                parse_mode="HTML"
            )
        except:
            pass
        
        await callback.answer("✅ Выплата отправлена!")
    else:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        await callback.message.edit_text(
            f"❌ <b>Ошибка выплаты!</b>\n\n"
            f"👤 Пользователь: {user_id}\n"
            f"📊 Видео ID: {video_id}\n"
            f"💰 Сумма: {payout_amount:.2f} ₽\n\n"
            f"❌ Ошибка: {error_msg}",
            parse_mode="HTML"
        )
        await callback.answer(f"❌ Ошибка: {error_msg}", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_payout_"))
async def admin_reject_payout(callback: CallbackQuery):
    """Админ отклоняет выплату для Bronze пользователя"""
    from core import config
    
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    video_id = int(callback.data.split("_")[3])
    
    # Получаем информацию о видео
    video = await db.get_video_with_details(video_id)
    
    if not video:
        await callback.answer("❌ Видео не найдено!", show_alert=True)
        return
    
    user_id = video['user_id']
    user = await db.get_user(user_id)
    
    await callback.message.edit_text(
        f"❌ <b>Выплата отклонена</b>\n\n"
        f"👤 Пользователь: {user.get('full_name', 'Неизвестно')}\n"
        f"🆔 ID: {user_id}\n"
        f"📊 Видео ID: {video_id}\n\n"
        f"Запрос на выплату был отклонен администратором.",
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            user_id,
            f"❌ <b>Запрос на выплату отклонен</b>\n\n"
            f"📊 Видео ID: {video_id}\n\n"
            f"Ваш запрос на выплату был отклонен администратором.\n"
            f"Для получения дополнительной информации свяжитесь с поддержкой.",
            parse_mode="HTML"
        )
    except:
        pass
    
    await callback.answer("❌ Выплата отклонена")
