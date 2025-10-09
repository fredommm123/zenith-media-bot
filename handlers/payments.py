from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.database import Database
from core.utils import format_currency, send_to_admin_chat
from core.crypto_pay import calculate_usdt_amount, send_payment
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
    
    # Проверка минимального баланса (1$ в рублях)
    usdt_amount = await calculate_usdt_amount(balance)
    min_usdt = 1.0
    
    if balance <= 0:
        # Получаем курс для рассчета минимума в рублях
        from core.crypto_pay import get_exchange_rate_rub_to_usdt
        rate = await get_exchange_rate_rub_to_usdt()
        min_rub = (1.0 / rate) if rate else 95.0  # примерно 95 рублей за 1 USDT
        
        await message.answer(
            f"💼 <b>Вывод средств</b>\n\n"
            f"💰 Ваш баланс: {format_currency(balance)}\n\n"
            f"❌ Недостаточно средств для вывода\n"
            f"Минимум для вывода: <b>{min_rub:.2f} ₽</b>",
            parse_mode="HTML"
        )
        return
    
    if usdt_amount and usdt_amount < min_usdt:
        # Рассчитываем минимум в рублях
        from core.crypto_pay import get_exchange_rate_rub_to_usdt
        rate = await get_exchange_rate_rub_to_usdt()
        min_rub = (1.0 / rate) if rate else 95.0
        
        await message.answer(
            f"💼 <b>Вывод средств</b>\n\n"
            f"💰 Ваш баланс: {format_currency(balance)}\n"
            f"💵 В USDT: ~{usdt_amount:.4f} USDT\n\n"
            f"⚠️ Минимум для вывода: <b>{min_rub:.2f} ₽</b>\n"
            f"Продолжайте загружать видео для накопления!",
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
        f"✅ Минимум 1 USDT - можно выводить!\n"
        f"Нажмите кнопку ниже для вывода:",
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
    
    # Конвертируем в USDT
    usdt_amount = await calculate_usdt_amount(balance)
    
    if not usdt_amount or usdt_amount < 1.0:
        await callback.answer("❌ Минимум 1 USDT для вывода!", show_alert=True)
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
        await db.update_balance(callback.from_user.id, -balance)
        
        await callback.message.edit_text(
            f"✅ <b>Выплата успешно выполнена!</b>\n\n"
            f"💰 Сумма: {format_currency(balance)}\n"
            f"💵 Получено: ~{usdt_amount:.4f} USDT\n\n"
            f"💼 Деньги отправлены на ваш @CryptoBot аккаунт.\n"
            f"Проверьте баланс в боте!",
            parse_mode="HTML"
        )
        
        # Уведомляем админов
        await send_to_admin_chat(
            f"💸 <b>Вывод с баланса</b>\n\n"
            f"👤 Пользователь: {user['full_name']} (@{user.get('username', 'нет')})\n"
            f"🆔 ID: {callback.from_user.id}\n"
            f"💰 Сумма: {format_currency(balance)}\n"
            f"💵 USDT: ~{usdt_amount:.4f}\n"
            f"✅ Успешно"
        )
        
        await callback.answer("✅ Выплата выполнена!")
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка выплаты</b>\n\n"
            f"⚠️ Причина: {result['error']}\n\n"
            f"Обратитесь в поддержку",
            parse_mode="HTML"
        )
        
        await callback.answer(f"❌ {result['error']}", show_alert=True)
