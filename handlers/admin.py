from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database import Database
from core.keyboards import admin_keyboard, withdrawal_action_keyboard
from core.utils import format_currency, format_timestamp, get_status_text
from core.crypto_pay import check_transfer_settings, get_app_balance, create_invoice, get_invoice_status
from core import config

router = Router()
db = Database(config.DATABASE_PATH)


class BroadcastStates(StatesGroup):
    waiting_for_message = State()


class TopUpStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_currency = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    stats = await db.get_stats()
    
    admin_text = (
        f"👑 <b>Админ панель</b>\n\n"
        f"📊 <b>Общая статистика:</b>\n"
        f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
        f"💰 Общий баланс: {format_currency(stats.get('total_balance', 0) or 0)}\n"
        f"🎬 Всего видео: {stats.get('total_videos', 0)}\n"
        f"👁 Всего просмотров: {stats.get('total_views', 0) or 0:,}\n"
        f"💸 Всего выведено: {format_currency(stats.get('total_withdrawn', 0) or 0)}\n"
        f"📋 Заявок на вывод: {stats.get('total_withdrawals', 0)}\n"
    )
    
    await message.answer(admin_text, reply_markup=admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    stats = await db.get_stats()
    
    stats_text = (
        f"📊 <b>Подробная статистика</b>\n\n"
        f"<b>👥 Пользователи:</b>\n"
        f"• Всего: {stats.get('total_users', 0)}\n"
        f"• Общий баланс: {format_currency(stats.get('total_balance', 0) or 0)}\n\n"
        f"<b>🎬 Видео:</b>\n"
        f"• Всего роликов: {stats.get('total_videos', 0)}\n"
        f"• Всего просмотров: {stats.get('total_views', 0) or 0:,}\n\n"
        f"<b>💰 Выплаты:</b>\n"
        f"• Завершенных выплат: {stats.get('total_withdrawals', 0)}\n"
        f"• Всего выведено: {format_currency(stats.get('total_withdrawn', 0) or 0)}\n"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals(callback: CallbackQuery):
    """Показать заявки на вывод"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    requests = await db.get_all_withdrawal_requests(status="pending")
    
    if not requests:
        await callback.message.edit_text(
            "📭 <b>Нет ожидающих заявок на вывод</b>",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    requests_text = f"💰 <b>Заявки на вывод ({len(requests)})</b>\n\n"
    
    for req in requests[:5]:  # Показываем первые 5
        created_at = format_timestamp(req['created_at'])
        requests_text += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{req['id']}</code>\n"
            f"👤 Пользователь: {req['full_name']} (@{req['username']})\n"
            f"💰 Сумма: <b>{format_currency(req['amount'])}</b>\n"
            f"💳 Способ: {req['payment_method']}\n"
            f"📋 Реквизиты: <code>{req['payment_details']}</code>\n"
            f"📅 Дата: {created_at}\n"
            f"\n/process_{req['id']} - обработать заявку\n"
        )
    
    if len(requests) > 5:
        requests_text += f"\n... и еще {len(requests) - 5} заявок"
    
    await callback.message.edit_text(requests_text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(F.text.startswith("/process_"))
async def process_withdrawal(message: Message):
    """Обработать заявку на вывод"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа!")
        return
    
    try:
        request_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды!")
        return
    
    # Получаем информацию о заявке
    requests = await db.get_all_withdrawal_requests(status="pending")
    request = next((r for r in requests if r['id'] == request_id), None)
    
    if not request:
        await message.answer("❌ Заявка не найдена или уже обработана!")
        return
    
    request_text = (
        f"💰 <b>Заявка на вывод #{request_id}</b>\n\n"
        f"👤 Пользователь: {request['full_name']} (@{request['username']})\n"
        f"🆔 User ID: <code>{request['user_id']}</code>\n"
        f"💰 Сумма: <b>{format_currency(request['amount'])}</b>\n"
        f"💳 Способ: {request['payment_method']}\n"
        f"📋 Реквизиты: <code>{request['payment_details']}</code>\n"
        f"📅 Дата создания: {format_timestamp(request['created_at'])}\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(
        request_text,
        reply_markup=withdrawal_action_keyboard(request_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("approve_withdrawal_"))
async def approve_withdrawal(callback: CallbackQuery):
    """Одобрить заявку на вывод"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    request_id = int(callback.data.split("_")[2])
    
    # Обрабатываем заявку
    await db.process_withdrawal(request_id, success=True)
    
    await callback.message.edit_text(
        f"✅ <b>Заявка #{request_id} одобрена!</b>\n\n"
        f"Средства списаны с баланса пользователя.",
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    requests = await db.get_all_withdrawal_requests(status="completed")
    request = next((r for r in requests if r['id'] == request_id), None)
    
    if request:
        try:
            await callback.bot.send_message(
                request['user_id'],
                f"✅ <b>Ваша заявка на вывод одобрена!</b>\n\n"
                f"🆔 ID заявки: <code>{request_id}</code>\n"
                f"💰 Сумма: <b>{format_currency(request['amount'])}</b>\n"
                f"💳 Способ: {request['payment_method']}\n\n"
                f"Средства отправлены на указанные реквизиты.",
                parse_mode="HTML"
            )
        except:
            pass
    
    await callback.answer("✅ Заявка одобрена!")


@router.callback_query(F.data.startswith("reject_withdrawal_"))
async def reject_withdrawal(callback: CallbackQuery):
    """Отклонить заявку на вывод"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    request_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о заявке перед отклонением
    requests = await db.get_all_withdrawal_requests(status="pending")
    request = next((r for r in requests if r['id'] == request_id), None)
    
    # Обрабатываем заявку
    await db.process_withdrawal(request_id, success=False)
    
    await callback.message.edit_text(
        f"❌ <b>Заявка #{request_id} отклонена!</b>",
        parse_mode="HTML"
    )
    
    # Уведомляем пользователя
    if request:
        try:
            await callback.bot.send_message(
                request['user_id'],
                f"❌ <b>Ваша заявка на вывод отклонена</b>\n\n"
                f"🆔 ID заявки: <code>{request_id}</code>\n"
                f"💰 Сумма: <b>{format_currency(request['amount'])}</b>\n\n"
                f"Свяжитесь с поддержкой для уточнения причины.",
                parse_mode="HTML"
            )
        except:
            pass
    
    await callback.answer("❌ Заявка отклонена!")


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям.\n\n"
        "⚠️ Поддерживается текст, фото, видео.",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    """Отправить рассылку"""
    if not is_admin(message.from_user.id):
        return
    
    # Здесь нужно получить всех пользователей
    # Для упрощения используем заглушку
    await message.answer("⏳ Рассылка запущена...")
    
    # В реальном боте здесь должна быть логика рассылки всем пользователям
    # Например:
    # users = await db.get_all_users()
    # success = 0
    # failed = 0
    # for user in users:
    #     try:
    #         await message.bot.copy_message(user['user_id'], message.chat.id, message.message_id)
    #         success += 1
    #     except:
    #         failed += 1
    
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Отправлено: 0\n"
        f"❌ Не доставлено: 0",
        parse_mode="HTML"
    )
    await state.clear()


# ========================
# МОДЕРАЦИЯ ВИДЕО
# ========================

@router.callback_query(F.data.startswith("approve_video_"))
async def approve_video(callback: CallbackQuery):
    """Одобрить видео"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    video_id = int(callback.data.split("_")[2])

    # Получаем информацию о видео
    video = await db.get_video(video_id)
    if not video:
        await callback.answer("❌ Видео не найдено!", show_alert=True)
        return

    user = await db.get_user(video['user_id'])
    tier = user.get('tier', 'bronze') if user else 'bronze'

    platform = video.get('platform', 'tiktok')
    author = video.get('video_author') or video.get('author', 'Неизвестно')
    views = video['views']

    from handlers.payouts import calculate_payout_amount
    from core.crypto_pay import calculate_usdt_amount, send_payment

    payout_amount = await calculate_payout_amount(views, platform, video['user_id'], video_id)
    usdt_amount = await calculate_usdt_amount(payout_amount)
    if not usdt_amount:
        usdt_amount = 0

    # Проверяем сумму в USDT (для TikTok)
    min_usdt_for_payout = 1.0  # Минимум 1 USDT для прямой выплаты
    
    # Если TikTok и меньше 1$ - начисляем на баланс
    if platform == 'tiktok' and usdt_amount < min_usdt_for_payout:
        await db.update_video_status(video_id, "approved")
        await db.update_user_balance(video['user_id'], payout_amount, operation='add')  # Начисляем на баланс
        
        await callback.message.edit_text(
            f"✅ <b>Видео #{video_id} одобрено!</b>\n\n"
            f"👤 Пользователь: ID {video['user_id']}\n"
            f"📺 Автор: @{author}\n"
            f"🎵 Платформа: TikTok\n"
            f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n\n"
            f"💼 Меньше 1$ - начислено на баланс",
            parse_mode="HTML"
        )
        
        await callback.bot.send_message(
            video['user_id'],
            f"✅ <b>Ваше TikTok видео одобрено!</b>\n\n"
            f"🆔 ID видео: <code>{video_id}</code>\n"
            f"💰 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n\n"
            f"💼 <b>Начислено на баланс</b> (меньше 1$)\n"
            f"Выводите с баланса от 1$ через кнопку \"💰 Вывод средств\"",
            parse_mode="HTML"
        )
        await callback.answer("✅ Одобрено! Деньги на баланс")
        return
    
    # Для всех остальных случаев - прямая выплата
    # Получаем username для платежа
    username = user.get('username') if user else None
    if not username:
        username = f"user_{video['user_id']}"
    
    # Генерируем spend_id
    from datetime import datetime
    spend_id = f"video_{video_id}_{datetime.now().timestamp()}"
    
    if tier == 'gold':
        # Gold-tier: автоматическая выплата
        await db.update_video_status(video_id, "approved")
        
        payment_result = await send_payment(
            user_id=video['user_id'],
            username=username,
            spend_id=spend_id,
            amount_usdt=usdt_amount,
            comment=f"Выплата за видео #{video_id}"
        )
        
        if payment_result['success']:
            await callback.bot.send_message(
                video['user_id'],
                f"✅ <b>Ваше видео одобрено!</b>\n\n"
                f"🆔 ID видео: <code>{video_id}</code>\n"
                f"🔗 {video['video_url']}\n\n"
                f"💵 Выплата: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)",
                parse_mode="HTML"
            )
            await callback.answer("✅ Видео одобрено и выплата отправлена!")
        else:
            await callback.answer(f"❌ Ошибка: {payment_result.get('error')}", show_alert=True)
    else:
        # Bronze-tier: только одобрение, БЕЗ автоматической выплаты
        await db.update_video_status(video_id, "approved")
        await callback.message.edit_text(
            f"✅ <b>Видео #{video_id} одобрено!</b>\n\n"
            f"👤 Пользователь: ID {video['user_id']}\n"
            f"📺 Автор: @{author}\n"
            f"🔗 {video['video_url']}\n\n"
            f"💵 Сумма: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n\n"
            f"⏳ <b>Выплата НЕ отправлена!</b>\n"
            f"Bronze пользователь должен запросить выплату кнопкой \"💰 Запросить выплату\"",
            parse_mode="HTML"
        )
        await callback.bot.send_message(
            video['user_id'],
            f"✅ <b>Ваше видео одобрено!</b>\n\n"
            f"🆔 ID видео: <code>{video_id}</code>\n"
            f"🔗 {video['video_url']}\n\n"
            f"💵 Начислено: {payout_amount:.2f} ₽ (~{usdt_amount:.4f} USDT)\n\n"
            f"💰 Для вывода нажмите кнопку \"💰 Запросить выплату\" в меню видео.",
            parse_mode="HTML"
        )
        await callback.answer("✅ Видео одобрено!")


@router.callback_query(F.data == "admin_tiers")
async def admin_tiers_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления статусами пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    tier_text = (
        f"🥉🥇 <b>Управление статусами пользователей</b>\n\n"
        f"<b>Доступные статусы:</b>\n"
        f"🥉 <b>Bronze (Бронзовый)</b>\n"
        f"  • Вывод после одобрения админом\n"
        f"  • Стандартный уровень\n\n"
        f"🥇 <b>Gold (Золотой)</b>\n"
        f"  • Автоматическая выплата\n"
        f"  • Для проверенных пользователей\n\n"
        f"<b>Команды:</b>\n"
        f"<code>/set_tier USER_ID bronze</code> - установить Bronze\n"
        f"<code>/set_tier USER_ID gold</code> - установить Gold\n"
        f"<code>/get_tier USER_ID</code> - посмотреть статус\n\n"
        f"<b>Пример:</b>\n"
        f"<code>/set_tier 7916638098 gold</code>"
    )
    
    from core.keyboards import admin_keyboard
    await callback.message.edit_text(tier_text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_topup")
async def admin_topup_menu(callback: CallbackQuery, state: FSMContext):
    """Меню пополнения баланса приложения"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    # Получаем текущий баланс
    balance = await get_app_balance()
    
    balance_text = "💰 <b>Баланс приложения:</b>\n"
    if balance:
        for currency, amount in balance.items():
            if amount > 0:
                balance_text += f"  • {currency}: {amount:.2f}\n"
        if not any(amount > 0 for amount in balance.values()):
            balance_text += "  • Баланс пуст\n"
    else:
        balance_text += "  • Ошибка получения баланса\n"
    
    topup_text = (
        f"💳 <b>Пополнение баланса приложения</b>\n\n"
        f"{balance_text}\n"
        f"<b>Быстрое пополнение:</b>\n"
        f"<code>/create_invoice 50 USDT</code> - 50 USDT\n"
        f"<code>/create_invoice 100 USDT</code> - 100 USDT\n"
        f"<code>/create_invoice 1 TON</code> - 1 TON\n\n"
        f"<b>Произвольная сумма:</b>\n"
        f"<code>/create_invoice &lt;сумма&gt; &lt;валюта&gt;</code>\n\n"
        f"<b>Пример:</b>\n"
        f"<code>/create_invoice 75.50 USDT</code>\n\n"
        f"<b>Поддерживаемые валюты:</b>\n"
        f"USDT, TON, BTC, ETH, USDC, TRX, SOL, BNB и др.\n\n"
        f"<b>Проверить статус счета:</b>\n"
        f"<code>/check_invoice &lt;invoice_id&gt;</code>"
    )
    
    from core.keyboards import admin_keyboard
    await callback.message.edit_text(topup_text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(Command("check_crypto"))
async def check_crypto_settings(message: Message):
    """Проверка настроек Crypto Bot"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа!")
        return
    
    await message.answer("🔄 Проверяю настройки Crypto Bot...")
    
    settings = await check_transfer_settings()
    
    if settings.get("errors"):
        error_text = "❌ <b>Обнаружены проблемы:</b>\n\n"
        for error in settings["errors"]:
            error_text += f"• {error}\n"
        await message.answer(error_text, parse_mode="HTML")
    
    info_text = (
        f"🤖 <b>Настройки Crypto Bot</b>\n\n"
        f"📱 <b>Приложение:</b>\n"
        f"  • ID: <code>{settings.get('app_id', 'N/A')}</code>\n"
        f"  • Название: {settings.get('name', 'N/A')}\n"
        f"  • Bot: @{settings.get('payment_processing_bot_username', 'N/A')}\n\n"
        f"💰 <b>Баланс:</b>\n"
    )
    
    balance = settings.get("balance", {})
    if balance:
        for currency, amount in balance.items():
            info_text += f"  • {currency}: {amount:.2f}\n"
    else:
        info_text += "  • Баланс пуст\n"
    
    info_text += "\n"
    
    if settings.get("has_balance"):
        info_text += "✅ Баланс USDT доступен\n"
    else:
        info_text += (
            "⚠️ <b>Баланс USDT = 0</b>\n\n"
            "<b>Как пополнить:</b>\n"
            "1. Открой @CryptoBot\n"
            "2. Wallet → USDT\n"
            "3. Пополни баланс\n"
            "4. My Apps → выбери приложение\n"
            "5. Transfer → пополни баланс приложения\n\n"
        )
    
    info_text += (
        "<b>Если переводы не работают:</b>\n"
        "1. @CryptoBot → My Apps\n"
        "2. Выбери приложение (ID: {app_id})\n"
        "3. Settings → Security\n"
        "4. Включи 'Allow Transfers'"
    ).format(app_id=settings.get('app_id', 'N/A'))
    
    await message.answer(info_text, parse_mode="HTML")


@router.message(Command("create_invoice"))
async def create_topup_invoice(message: Message):
    """
    Создать счет для пополнения баланса приложения
    Использование: /create_invoice <сумма> <валюта>
    Пример: /create_invoice 50 USDT
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа!")
        return
    
    try:
        # Парсим аргументы
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "<b>Использование:</b>\n"
                "<code>/create_invoice &lt;сумма&gt; [валюта]</code>\n\n"
                "<b>Примеры:</b>\n"
                "<code>/create_invoice 50 USDT</code>\n"
                "<code>/create_invoice 100 TON</code>\n"
                "<code>/create_invoice 0.001 BTC</code>\n\n"
                "<b>Поддерживаемые валюты:</b>\n"
                "USDT, TON, BTC, ETH, USDC, TRX, SOL и др.",
                parse_mode="HTML"
            )
            return
        
        amount = float(args[1])
        currency = args[2].upper() if len(args) > 2 else "USDT"
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0!")
            return
        
        # Создаем счет
        await message.answer(f"🔄 Создаю счет на {amount} {currency}...")
        
        result = await create_invoice(
            amount=amount,
            currency=currency,
            description=f"Пополнение баланса Zenith Media"
        )
        
        if result["success"]:
            response_text = (
                f"✅ <b>Счет создан!</b>\n\n"
                f"💰 <b>Сумма:</b> {amount} {currency}\n"
                f"🆔 <b>Invoice ID:</b> <code>{result['invoice_id']}</code>\n"
                f"📊 <b>Статус:</b> {result['status']}\n\n"
                f"<b>Для оплаты используй одну из ссылок:</b>\n\n"
                f"🤖 <b>Через бота:</b>\n{result['bot_invoice_url']}\n\n"
            )
            
            if result.get('mini_app_invoice_url'):
                response_text += f"📱 <b>Через Mini App:</b>\n{result['mini_app_invoice_url']}\n\n"
            
            response_text += (
                f"<b>Проверить статус:</b>\n"
                f"<code>/check_invoice {result['invoice_id']}</code>"
            )
            
            await message.answer(response_text, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await message.answer(result["error"], parse_mode="HTML")
    
    except ValueError:
        await message.answer("❌ Неверная сумма! Используй число (например: 50 или 0.001)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("check_invoice"))
async def check_invoice_status(message: Message):
    """
    Проверить статус счета
    Использование: /check_invoice <invoice_id>
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа!")
        return
    
    try:
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer(
                "❌ <b>Укажи ID счета!</b>\n\n"
                "<b>Использование:</b>\n"
                "<code>/check_invoice &lt;invoice_id&gt;</code>\n\n"
                "<b>Пример:</b>\n"
                "<code>/check_invoice 12345</code>",
                parse_mode="HTML"
            )
            return
        
        invoice_id = int(args[1])
        
        await message.answer(f"🔄 Проверяю статус счета {invoice_id}...")
        
        result = await get_invoice_status(invoice_id)
        
        if result["success"]:
            status_emoji = {
                "active": "⏳",
                "paid": "✅",
                "expired": "❌"
            }.get(result["status"], "❓")
            
            status_text = {
                "active": "Ожидает оплаты",
                "paid": "Оплачен",
                "expired": "Истек"
            }.get(result["status"], result["status"])
            
            response_text = (
                f"{status_emoji} <b>Статус счета</b>\n\n"
                f"🆔 <b>Invoice ID:</b> <code>{invoice_id}</code>\n"
                f"💰 <b>Сумма:</b> {result['amount']} {result['currency']}\n"
                f"📊 <b>Статус:</b> {status_text}\n"
            )
            
            if result.get("paid_at"):
                response_text += f"✅ <b>Оплачен:</b> {result['paid_at']}\n"
            
            if result["status"] == "paid":
                response_text += "\n🎉 <b>Баланс пополнен!</b>"
            elif result["status"] == "active":
                response_text += "\n⏳ Ожидаю оплату..."
            
            await message.answer(response_text, parse_mode="HTML")
        else:
            await message.answer(result["error"], parse_mode="HTML")
    
    except ValueError:
        await message.answer("❌ Invoice ID должен быть числом!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
