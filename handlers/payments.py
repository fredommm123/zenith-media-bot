from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import Database
from core.utils import format_currency, send_to_admin_chat
from core.crypto_pay import calculate_usdt_amount, send_payment, get_exchange_rate_rub_to_usdt
from core import config
import logging

router = Router()
db = Database(config.DATABASE_PATH)
logger = logging.getLogger(__name__)


@router.message(F.text == "💰 Вывод средств")
async def show_withdrawal_menu(message: Message):
    """Показать меню вывода средств с баланса"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Вы не зарегистрированы! Используйте /start", parse_mode="HTML")
        return
    
    balance = user['balance']
    
    # Проверка минимального баланса (CryptoBot требует >=0.1 USDT)
    usdt_amount = await calculate_usdt_amount(balance)
    if usdt_amount is None:
        await message.answer(
            "❌ Не удалось получить курс USDT. Попробуйте позже.",
            parse_mode="HTML"
        )
        return

    min_usdt = 0.1
    rate = await get_exchange_rate_rub_to_usdt()
    min_rub = (min_usdt / rate) if rate else 9.0
    
    if balance <= 0 or usdt_amount < min_usdt:
        await message.answer(
            f"💼 <b>Вывод средств</b>\n\n"
            f"💰 Ваш баланс: {format_currency(balance)}\n"
            f"💵 В USDT: ~{usdt_amount:.4f} USDT\n\n"
            f"❌ Минимальная сумма для мгновенного вывода: <b>{min_rub:.2f} ₽</b> (~{min_usdt:.1f} USDT)",
            parse_mode="HTML"
        )
        return
    
    # Показываем кнопку вывода
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Вывести весь баланс", callback_data="withdraw_balance")]
    ])
    
    await message.answer(
        f"💼 <b>Вывод средств с баланса</b>\n\n"
        f"💰 Доступно: {format_currency(balance)}\n"
        f"💵 В USDT: ~{usdt_amount:.4f} USDT\n\n"
        f"⚡ Выводим мгновенно на @CryptoBot после нажатия кнопки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "withdraw_balance")
async def process_balance_withdrawal(callback: CallbackQuery):
    """Обработка запроса на вывод баланса"""
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден!", show_alert=True)
        return
    
    balance = user['balance']
    
    if balance <= 0:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Конвертируем в USDT и проверяем минимум CryptoBot
    usdt_amount = await calculate_usdt_amount(balance)
    if usdt_amount is None:
        await callback.answer("❌ Не удалось получить курс USDT. Попробуйте позже", show_alert=True)
        return

    min_usdt = 0.1
    if usdt_amount < min_usdt:
        rate = await get_exchange_rate_rub_to_usdt()
        min_rub = (min_usdt / rate) if rate else 9.0
        await callback.answer(
            f"❌ Минимум для вывода: {min_usdt:.1f} USDT (~{min_rub:.2f} ₽)",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        f"⏳ <b>Обработка вывода...</b>\n\n"
        f"💰 Сумма: {format_currency(balance)}\n"
        f"💵 В USDT: ~{usdt_amount:.4f} USDT",
        parse_mode="HTML"
    )
    
    # Отправляем USDT через Crypto Pay
    import uuid
    spend_id = f"balance_{callback.from_user.id}_{uuid.uuid4().hex[:8]}"
    
    result = await send_payment(
        user_id=callback.from_user.id,
        username=user.get('username', 'unknown'),
        spend_id=spend_id,
        amount_rub=balance,
        comment="Вывод с баланса"
    )
    
    if result['success']:
        # Списываем с баланса
        await db.update_user_balance(callback.from_user.id, balance, operation='subtract')
        
        await callback.message.edit_text(
            f"✅ <b>Мгновенный вывод выполнен!</b>\n\n"
            f"💰 Сумма: {format_currency(balance)}\n"
            f"💵 Отправлено: ~{usdt_amount:.4f} USDT\n\n"
            f"⚡ Средства уже на вашем @CryptoBot аккаунте.",
            parse_mode="HTML"
        )
        
        # Получаем статистику по видео для админа
        videos = await db.get_user_videos(callback.from_user.id)
        approved_videos = [v for v in videos if v['status'] == 'approved']
        
        videos_info = ""
        for i, video in enumerate(approved_videos[:5], 1):  # Показываем последние 5
            videos_info += (
                f"\n{i}. [{video.get('platform', 'N/A').upper()}] "
                f"{video.get('views', 0):,} 👁 - "
                f"{video.get('video_url', 'нет ссылки')}"
            )
        
        if len(approved_videos) > 5:
            videos_info += f"\n... и еще {len(approved_videos) - 5} видео"
        
        # Уведомляем админов
        await send_to_admin_chat(
            callback.bot,
            f"💸 <b>МГНОВЕННЫЙ ВЫВОД</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Пользователь:</b>\n"
            f"  • Имя: {user['full_name']}\n"
            f"  • Username: @{user.get('username', 'нет')}\n"
            f"  • ID: {callback.from_user.id}\n\n"
            f"💰 <b>Сумма вывода:</b> {format_currency(balance)} (~{usdt_amount:.4f} USDT)\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"  • Всего видео: {len(videos)}\n"
            f"  • Одобрено: {len(approved_videos)}\n"
            f"  • Реферальный доход: {user.get('referral_earnings', 0):.2f} ₽\n"
            f"📹 <b>Последние видео:</b>{videos_info}\n\n"
            f"⚡ Средства отправлены автоматически",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Выплата выполнена!")
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await callback.message.edit_text(
            f"❌ <b>Ошибка мгновенного вывода</b>\n\n"
            f"⚠️ Причина: {error_msg}\n\n"
            f"Попробуйте позже или обратитесь в поддержку.",
            parse_mode="HTML"
        )
        
        await callback.answer(f"❌ {error_msg}", show_alert=True)
