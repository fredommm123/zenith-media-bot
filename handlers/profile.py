from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database import Database
from core.keyboards import (
    main_menu_keyboard, profile_keyboard, confirm_keyboard, cancel_keyboard
)
from core.utils import format_currency
from core import config

router = Router()
db = Database(config.DATABASE_PATH)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    user = await db.get_user(message.from_user.id)
    
    # Проверяем реферальный код
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        from core.utils import parse_referral_code
        referrer_id = parse_referral_code(message.text.split()[1])
    
    if not user:
        # Регистрируем нового пользователя
        await db.add_user(
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name,
            referrer_id=referrer_id
        )
        
        welcome_text = (
            "🎉 <b>Добро пожаловать в ZenithMedia Bot!</b>\n\n"
            "Ваш помощник для монетизации видеоконтента\n\n"
            "Выберите действие:"
        )
    else:
        welcome_text = (
            "👋 <b>С возвращением!</b>\n\n"
            "Выберите действие:"
        )
    
    await message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    payment_methods = await db.get_payment_methods(message.from_user.id)
    referral_stats = await db.get_referral_stats(message.from_user.id)
    tiktok = await db.get_user_tiktok(message.from_user.id)
    youtube = await db.get_user_youtube(message.from_user.id)
    
    payment_text = "\n".join([f"  • {pm['method_type']}" for pm in payment_methods]) if payment_methods else "Не добавлены"
    
    # TikTok статус
    if tiktok:
        verified_emoji = "✅" if tiktok['is_verified'] else "⏳"
        tiktok_text = f"{verified_emoji} <code>@{tiktok['username']}</code>"
    else:
        tiktok_text = "Не привязан"
    
    # YouTube статус
    if youtube:
        verified_emoji = "✅" if youtube['is_verified'] else "⏳"
        youtube_text = f"{verified_emoji} <b>{youtube['channel_name']}</b>"
    else:
        youtube_text = "Не привязан"
    
    from core.utils import generate_referral_link
    bot_username = (await message.bot.me()).username
    referral_link = generate_referral_link(bot_username, message.from_user.id)
    
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🎭 <b>Имя:</b> {user['full_name']}\n"
        f"🆔 <b>ID:</b> <code>{user['user_id']}</code>\n"
        f"📱 <b>Username:</b> @{user['username'] or 'не указан'}\n\n"
        f"🎵 <b>TikTok:</b> {tiktok_text}\n"
        f"📺 <b>YouTube:</b> {youtube_text}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"💰 Баланс: <b>{format_currency(user['balance'])}</b>\n"
        f"🎬 Роликов: {user['total_videos']}\n"
        f"👁 Общих просмотров: {user['total_views']:,}\n"
        f"📤 Выведено всего: {format_currency(user['total_withdrawn'])}\n\n"
        f"💳 <b>Способы выплат:</b>\n{payment_text}\n\n"
        f"👥 <b>Реферальная программа:</b>\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n"
        f"💵 Заработано с рефералов: <b>{format_currency(referral_stats['total_earnings'])}</b>\n"
        f"👤 Рефералов: {referral_stats['total_referrals']}"
    )
    
    await message.answer(profile_text, reply_markup=profile_keyboard(has_tiktok=bool(tiktok), has_youtube=bool(youtube), balance=user['balance']), parse_mode="HTML")


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery):
    """Вернуться к профилю"""
    await callback.message.delete()
    
    user = await db.get_user(callback.from_user.id)
    payment_methods = await db.get_payment_methods(callback.from_user.id)
    referral_stats = await db.get_referral_stats(callback.from_user.id)
    tiktok = await db.get_user_tiktok(callback.from_user.id)
    youtube = await db.get_user_youtube(callback.from_user.id)
    
    payment_text = "\n".join([f"  • {pm['method_type']}" for pm in payment_methods]) if payment_methods else "Не добавлены"
    
    # TikTok статус
    if tiktok:
        verified_emoji = "✅" if tiktok['is_verified'] else "⏳"
        tiktok_text = f"{verified_emoji} <code>@{tiktok['username']}</code>"
    else:
        tiktok_text = "Не привязан"
    
    # YouTube статус
    if youtube:
        verified_emoji = "✅" if youtube['is_verified'] else "⏳"
        youtube_text = f"{verified_emoji} <b>{youtube['channel_name']}</b>"
    else:
        youtube_text = "Не привязан"
    
    from core.utils import generate_referral_link
    bot_username = (await callback.bot.me()).username
    referral_link = generate_referral_link(bot_username, callback.from_user.id)
    
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🎭 <b>Имя:</b> {user['full_name']}\n"
        f"🆔 <b>ID:</b> <code>{user['user_id']}</code>\n"
        f"📱 <b>Username:</b> @{user['username'] or 'не указан'}\n\n"
        f"🎵 <b>TikTok:</b> {tiktok_text}\n"
        f"📺 <b>YouTube:</b> {youtube_text}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"💰 Баланс: <b>{format_currency(user['balance'])}</b>\n"
        f"🎬 Роликов: {user['total_videos']}\n"
        f"👁 Общих просмотров: {user['total_views']:,}\n"
        f"📤 Выведено всего: {format_currency(user['total_withdrawn'])}\n\n"
        f"💳 <b>Способы выплат:</b>\n{payment_text}\n\n"
        f"👥 <b>Реферальная программа:</b>\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{referral_link}</code>\n"
        f"💵 Заработано с рефералов: <b>{format_currency(referral_stats['total_earnings'])}</b>\n"
        f"👤 Рефералов: {referral_stats['total_referrals']}"
    )
    
    await callback.message.answer(profile_text, reply_markup=profile_keyboard(has_tiktok=bool(tiktok), has_youtube=bool(youtube), balance=user['balance']), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_action(callback: CallbackQuery):
    """Отмена действия"""
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_state(callback: CallbackQuery, state: FSMContext):
    """Отмена состояния"""
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
