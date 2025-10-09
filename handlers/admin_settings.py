"""Административные настройки для управления ставками и уровнями"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database import Database
from core.config import ADMIN_IDS

from core.utils import send_to_admin_chat
import logging

logger = logging.getLogger(__name__)
router = Router()


class SetYouTubeRate(StatesGroup):
    waiting_for_rate = State()


class SetUserTier(StatesGroup):
    waiting_for_tier = State()


@router.message(Command("set_youtube_rate"))
async def cmd_set_youtube_rate(message: Message, state: FSMContext):
    """Установить ставку для YouTube канала: /set_youtube_rate user_id rate"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Используй: /set_youtube_rate <user_id> <ставка>\n"
            "Пример: /set_youtube_rate 123456789 75"
        )
        return
    
    try:
        user_id = int(args[1])
        rate = float(args[2])
        
        if rate <= 0:
            await message.answer("❌ Ставка должна быть больше 0!")
            return
        
        db = Database("bot_database.db")
        
        # Проверяем, есть ли у пользователя YouTube канал
        channel_info = await db.get_youtube_channel_info(user_id)
        if not channel_info:
            await message.answer(f"❌ У пользователя {user_id} нет привязанного YouTube канала!")
            return
        
        # Устанавливаем ставку
        success = await db.set_youtube_rate(user_id, rate)
        
        if success:
            await message.answer(
                f"✅ Ставка установлена!\n\n"
                f"👤 User ID: {user_id}\n"
                f"📺 Канал: {channel_info['channel_name']}\n"
                f"💰 Новая ставка: {rate}₽ за 1000 просмотров"
            )
            logger.info(f"Админ установил ставку {rate}₽/1K для user_id={user_id}")
        else:
            await message.answer("❌ Ошибка при установке ставки!")
    
    except ValueError:
        await message.answer("❌ User ID и ставка должны быть числами!")
    except Exception as e:
        logger.error(f"Ошибка в set_youtube_rate: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("set_tier"))
async def cmd_set_tier(message: Message):
    """Установить уровень пользователя: /set_tier user_id bronze/gold"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Используй: /set_tier <user_id> <bronze/gold>\n"
            "Пример: /set_tier 123456789 gold"
        )
        return
    
    try:
        user_id = int(args[1])
        tier = args[2].lower()
        
        if tier not in ['bronze', 'gold']:
            await message.answer("❌ Уровень может быть только 'bronze' или 'gold'!")
            return
        
        db = Database("bot_database.db")
        
        # Проверяем, существует ли пользователь
        user = await db.get_user(user_id)
        if not user:
            await message.answer(f"❌ Пользователь {user_id} не найден!")
            return
        
        # Устанавливаем уровень
        success = await db.set_user_tier(user_id, tier)
        
        if success:
            tier_emoji = "🥉" if tier == "bronze" else "🥇"
            tier_desc = "с одобрением админа" if tier == "bronze" else "автоматическая"
            
            await message.answer(
                f"✅ Уровень установлен!\n\n"
                f"👤 User ID: {user_id}\n"
                f"{tier_emoji} Уровень: {tier.upper()}\n"
                f"⏱ Вывод: {tier_desc}"
            )
            logger.info(f"Админ установил уровень {tier} для user_id={user_id}")
        else:
            await message.answer("❌ Ошибка при установке уровня!")
    
    except ValueError:
        await message.answer("❌ User ID должен быть числом!")
    except Exception as e:
        logger.error(f"Ошибка в set_tier: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("set_rate_"))
async def set_rate_for_video(callback: CallbackQuery, state: FSMContext):
    """Кнопка 'Установить ставку' в уведомлении о первом видео"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ Только для администратора!", show_alert=True)
        return
    
    try:
        video_id = int(callback.data.split("_")[2])
        
        db = Database("bot_database.db")
        video = await db.get_video_with_details(video_id)
        
        if not video:
            await callback.answer("❌ Видео не найдено!", show_alert=True)
            return
        
        # Сохраняем информацию в FSM включая ID сообщения
        await state.set_state(SetYouTubeRate.waiting_for_rate)
        await state.update_data(
            video_id=video_id,
            user_id=video['user_id'],
            admin_message_id=callback.message.message_id
        )
        
        await callback.message.answer(
            f"💰 Установка выплаты за YouTube видео\n\n"
            f"👤 User ID: {video['user_id']}\n"
            f"📺 Канал: {video.get('video_author', 'Неизвестно')}\n"
            f"👁 Просмотры: {video.get('views', 0):,}\n\n"
            f"💵 Отправь фиксированную сумму в рублях за это видео (например: 500)\n"
            f"ℹ️ Это будет выплата за видео независимо от просмотров"
        )
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Ошибка в set_rate_for_video: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.message(SetYouTubeRate.waiting_for_rate)
async def process_youtube_rate(message: Message, state: FSMContext):
    """Обработка введенной суммы за видео"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        amount = float(message.text)
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0! Попробуй еще раз:")
            return
        
        data = await state.get_data()
        user_id = data['user_id']
        video_id = data['video_id']
        
        db = Database("bot_database.db")
        
        # Одобряем видео и устанавливаем фиксированную сумму
        await db.update_video_status(video_id, 'approved')
        await db.update_video_earnings(video_id, amount)
        
        # Получаем информацию о видео и пользователе
        video = await db.get_video_with_details(video_id)
        user = await db.get_user(user_id)
        
        # Обновляем сообщение в админ-чате
        state_data = await state.get_data()
        admin_message_id = state_data.get('admin_message_id')
        
        updated_admin_text = (
            f"✅ <b>Выплата установлена и видео одобрено!</b>\n\n"
            f"💰 <b>Фиксированная выплата:</b> {amount:.2f}₽\n\n"
            f"📋 <b>Запрос на выплату</b>\n\n"
            f"👤 <b>Пользователь:</b>\n"
            f"• Имя: {user.get('full_name', 'Неизвестно')}\n"
            f"• Username: @{user.get('username', 'нет')}\n"
            f"• User ID: <code>{user_id}</code>\n"
            f"• Уровень: {('🥇 GOLD (24ч задержка)' if user.get('tier') == 'gold' else '🥉 BRONZE (24ч задержка)')}\n\n"
            f"📺 <b>Платформа:</b> YouTube\n"
            f"📺 <b>Канал:</b> {video.get('video_author', 'Неизвестно')}\n\n"
            f"📊 <b>Ставка:</b> {amount:.2f} ₽ за 1К просмотров\n\n"
            f"📈 <b>Информация о видео:</b>\n"
            f"• ID: {video_id}\n"
            f"• Название: {video.get('video_title', 'Неизвестно')[:30]}...\n"
            f"• URL: {video.get('video_url', 'Нет URL')}\n\n"
            f"📊 <b>Статистика видео:</b>\n"
            f"• 👁 Просмотры: {video.get('views', 0):,}\n"
            f"• ❤️ Лайки: {video.get('likes', 0)}\n"
            f"• 💬 Комментарии: {video.get('comments', 0)}\n\n"
            f"💸 <b>Расчет выплаты:</b>\n"
            f"• 💵 Фиксированная выплата за видео\n"
            f"• Сумма: {amount:.2f} ₽\n"
            f"• В USDT: ~{amount / 82:.2f} USDT"
        )
        
        try:
            if admin_message_id:
                # Пытаемся обновить существующее сообщение
                from core.utils import send_to_admin_chat
                await send_to_admin_chat(
                    message.bot,
                    updated_admin_text,
                    edit_message_id=admin_message_id
                )
        except Exception as e:
            logger.error(f"Не удалось обновить сообщение в админ-чате: {e}")
            # Если не удалось обновить, отправляем новое
            await message.answer(updated_admin_text, parse_mode="HTML")
        
        # Начисляем на баланс пользователя
        await db.update_user_balance(user_id, amount, operation='add')
        
        # Начисляем реферальные бонусы (10% от выплаты)
        if user and user.get('referrer_id'):
            referral_amount = amount * 0.10
            await db.add_referral_earning(
                referrer_id=user['referrer_id'],
                referred_id=user_id,
                amount=referral_amount
            )
            logger.info(f"Referral bonus {referral_amount:.2f} RUB credited to user {user['referrer_id']}")
        
        # Получаем новый баланс
        updated_user = await db.get_user(user_id)
        new_balance = updated_user.get('balance', 0)
        
        # Уведомляем пользователя
        try:
            await message.bot.send_message(
                user_id,
                f"✅ <b>Твое видео одобрено!</b>\n\n"
                f"🆔 ID видео: <code>{video_id}</code>\n"
                f"📺 {video.get('video_title', 'Видео')}\n"
                f"👁 Просмотры: {video.get('views', 0):,}\n\n"
                f"💵 Начислено: {amount:.2f} ₽\n\n"
                f"💰 <b>Деньги на вашем балансе!</b>\n"
                f"💼 Новый баланс: {new_balance:.2f} ₽\n\n"
                f"Выводите через \"💰 Вывод средств\" (минимум от 1$)",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю: {e}")
        
        logger.info(f"Админ установил выплату {amount}₽ для видео {video_id} (user_id={user_id})")
        
        await state.clear()
    
    except ValueError:
        await message.answer("❌ Введи число! Попробуй еще раз:")
    except Exception as e:
        logger.error(f"Ошибка в process_youtube_rate: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()


@router.message(Command("get_rate"))
async def cmd_get_rate(message: Message):
    """Посмотреть текущую ставку пользователя: /get_rate user_id"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Используй: /get_rate <user_id>\n"
            "Пример: /get_rate 123456789"
        )
        return
    
    try:
        user_id = int(args[1])
        db = Database("bot_database.db")
        
        # Проверяем YouTube канал
        channel_info = await db.get_youtube_channel_info(user_id)
        if not channel_info:
            await message.answer(f"❌ У пользователя {user_id} нет привязанного YouTube канала!")
            return
        
        rate = await db.get_youtube_rate(user_id)
        
        await message.answer(
            f"📊 Информация о ставке\n\n"
            f"👤 User ID: {user_id}\n"
            f"📺 Канал: {channel_info['channel_name']}\n"
            f"💰 Ставка: {rate}₽ за 1000 просмотров"
        )
    
    except ValueError:
        await message.answer("❌ User ID должен быть числом!")
    except Exception as e:
        logger.error(f"Ошибка в get_rate: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("get_tier"))
async def cmd_get_tier(message: Message):
    """Посмотреть текущий уровень пользователя: /get_tier user_id"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Используй: /get_tier <user_id>\n"
            "Пример: /get_tier 123456789"
        )
        return
    
    try:
        user_id = int(args[1])
        db = Database("bot_database.db")
        
        user = await db.get_user(user_id)
        if not user:
            await message.answer(f"❌ Пользователь {user_id} не найден!")
            return
        
        tier = await db.get_user_tier(user_id)
        tier_emoji = "🥉" if tier == "bronze" else "🥇"
        tier_desc = "с одобрением админа" if tier == "bronze" else "автоматическая"
        
        await message.answer(
            f"📊 Информация об уровне\n\n"
            f"👤 User ID: {user_id}\n"
            f"👤 Имя: {user['full_name']}\n"
            f"{tier_emoji} Уровень: {tier.upper()}\n"
            f"⏱ Вывод: {tier_desc}"
        )
    
    except ValueError:
        await message.answer("❌ User ID должен быть числом!")
    except Exception as e:
        logger.error(f"Ошибка в get_tier: {e}")
        await message.answer(f"❌ Ошибка: {e}")
