from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.database import Database
from core.keyboards import referral_keyboard
from core.utils import format_currency, generate_referral_link
from core import config

router = Router()
db = Database(config.DATABASE_PATH)


@router.message(F.text == "👥 Рефералы")
async def show_referral_info(message: Message):
    """Показать информацию о реферальной программе"""
    user = await db.get_user(message.from_user.id)
    stats = await db.get_referral_stats(message.from_user.id)
    
    bot_username = (await message.bot.me()).username
    referral_link = generate_referral_link(bot_username, message.from_user.id)
    
    referral_text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"👤 <b>Рефералов:</b> {stats['total_referrals']}\n"
        f"💰 <b>Общий заработок:</b> {format_currency(stats['total_earnings'])}\n"
        f"📊 <b>Средний заработок с реферала:</b> {format_currency(stats['avg_earnings'])}\n\n"
        f"🎯 <b>Как это работает:</b>\n"
        f"• Поделитесь своей ссылкой с друзьями\n"
        f"• Когда они регистрируются и получают выплаты за видео\n"
        f"• Вы получаете <b>{config.REFERRAL_PERCENT}%</b> от их заработка\n\n"
        f"🏆 <b>Ваши достижения:</b>\n"
    )
    
    # Добавляем достижения
    if stats['total_referrals'] == 0:
        referral_text += "Пока нет достижений\n\n"
    else:
        if stats['total_referrals'] >= 1:
            referral_text += "🥉 Первый реферал\n"
        if stats['total_referrals'] >= 10:
            referral_text += "🥈 10 рефералов\n"
        if stats['total_referrals'] >= 50:
            referral_text += "🥇 50 рефералов\n"
        if stats['total_referrals'] >= 100:
            referral_text += "💎 100 рефералов\n"
        referral_text += "\n"
    
    referral_text += (
        f"💡 <b>Совет:</b> Чем активнее ваши рефералы, тем больше вы зарабатываете!\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"Скопируйте ссылку и поделитесь ею!"
    )
    
    await message.answer(referral_text, reply_markup=referral_keyboard(referral_link), parse_mode="HTML")


@router.callback_query(F.data == "referral_stats")
async def show_referral_stats(callback: CallbackQuery):
    """Показать статистику рефералов"""
    stats = await db.get_referral_stats(callback.from_user.id)
    referrals = await db.get_referrals(callback.from_user.id)
    
    stats_text = (
        f"📊 <b>Статистика рефералов</b>\n\n"
        f"👥 <b>Всего приглашено:</b> {stats['total_referrals']} человек\n"
        f"💰 <b>Общий заработок:</b> {format_currency(stats['total_earnings'])}\n"
        f"📊 <b>Средний заработок с реферала:</b> {format_currency(stats['avg_earnings'])}\n\n"
    )
    
    if referrals:
        stats_text += "<b>Ваши рефералы:</b>\n\n"
        for ref in referrals[:10]:  # Показываем первых 10
            username = f"@{ref['username']}" if ref['username'] else ref['full_name']
            stats_text += (
                f"👤 {username}\n"
                f"   💰 Заработано с реферала: {format_currency(ref['earnings'])}\n\n"
            )
        
        if len(referrals) > 10:
            stats_text += f"... и еще {len(referrals) - 10} рефералов"
    else:
        stats_text += "У вас пока нет рефералов."
    
    await callback.message.edit_text(stats_text, reply_markup=referral_keyboard(""), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral_history")
async def show_referral_history(callback: CallbackQuery):
    """Показать историю реферальных начислений"""
    referrals = await db.get_referrals(callback.from_user.id)
    
    history_text = f"📜 <b>История реферальных начислений</b>\n\n"
    
    if not referrals:
        history_text += "История пуста."
    else:
        total_earnings = sum(ref['earnings'] for ref in referrals)
        history_text += f"💰 <b>Всего заработано:</b> {format_currency(total_earnings)}\n\n"
        
        for ref in referrals[:20]:  # Показываем последние 20
            username = f"@{ref['username']}" if ref['username'] else ref['full_name']
            history_text += (
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 Реферал: {username}\n"
                f"💰 Заработано: {format_currency(ref['earnings'])}\n"
            )
        
        if len(referrals) > 20:
            history_text += f"\n... и еще {len(referrals) - 20} записей"
    
    await callback.message.edit_text(history_text, reply_markup=referral_keyboard(""), parse_mode="HTML")
    await callback.answer()
