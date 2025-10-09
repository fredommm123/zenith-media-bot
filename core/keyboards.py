from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard_layout = [
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="📜 История")
        ],
        [
            KeyboardButton(text="🎬 Подать ролик"),
            KeyboardButton(text="👥 Рефералы")
        ],
        [
            KeyboardButton(text="💰 Вывод средств"),
            KeyboardButton(text="📄 Оферта")
        ]
    ]
    
    # Добавляем кнопку админа для администраторов
    if is_admin:
        keyboard_layout.append([
            KeyboardButton(text="👨‍💼 Админ-панель")
        ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_layout,
        resize_keyboard=True
    )
    return keyboard


def profile_keyboard(
    has_tiktok: bool = False,
    has_youtube: bool = False,
    balance: float = 0,
) -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()

    if not has_tiktok:
        builder.row(
            InlineKeyboardButton(text="🎵 Привязать TikTok", callback_data="add_tiktok")
        )

    if not has_youtube:
        builder.row(
            InlineKeyboardButton(text="📺 Привязать YouTube", callback_data="add_youtube")
        )

    builder.row(
        InlineKeyboardButton(text="🆓 Бесплатный ключ", callback_data="free_key_status")
    )

    builder.row(
        InlineKeyboardButton(text=" Назад в меню", callback_data="back_to_menu")
    )

    return builder.as_markup()


def confirm_keyboard(action: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    callback_yes = f"confirm_{action}_{item_id}" if item_id else f"confirm_{action}"
    callback_no = f"cancel_{action}_{item_id}" if item_id else f"cancel_{action}"
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=callback_yes),
        InlineKeyboardButton(text="❌ Нет", callback_data=callback_no)
    )
    return builder.as_markup()


def payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Способы выплат"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 СБП (Система Быстрых Платежей)", callback_data="payment_sbp")
    )
    builder.row(
        InlineKeyboardButton(text="₿ Litecoin (LTC)", callback_data="payment_ltc")
    )
    builder.row(
        InlineKeyboardButton(text="� USDT TRC20", callback_data="payment_usdt_trc20")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")
    )
    return builder.as_markup()


def payment_methods_list_keyboard(methods: list) -> InlineKeyboardMarkup:
    """Список способов выплат для удаления"""
    builder = InlineKeyboardBuilder()
    for method in methods:
        builder.row(
            InlineKeyboardButton(
                text=f"🗑️ {method['method_type']}: {method['details'][:20]}...",
                callback_data=f"delete_method_{method['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")
    )
    return builder.as_markup()


def pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    builder = InlineKeyboardBuilder()
    
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_page_{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_page_{page+1}"))
    
    builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """Клавиатура реферальной системы"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="referral_stats")
    )
    builder.row(
        InlineKeyboardButton(text="📜 История", callback_data="referral_history")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def withdrawal_keyboard(methods: list) -> InlineKeyboardMarkup:
    """Клавиатура для вывода средств"""
    builder = InlineKeyboardBuilder()
    for method in methods:
        builder.row(
            InlineKeyboardButton(
                text=f"{method['method_type']}: {method['details'][:20]}...",
                callback_data=f"withdraw_method_{method['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
    )
    return builder.as_markup()
def tiktok_verification_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения TikTok с кнопкой 'Поменял описание'"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Сменил описание", callback_data="tiktok_confirm_bio")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def video_platform_keyboard(has_tiktok: bool = False, has_youtube: bool = False) -> InlineKeyboardMarkup:
    """Выбор платформы для подачи видео"""
    builder = InlineKeyboardBuilder()
    
    if has_tiktok:
        builder.row(
            InlineKeyboardButton(text="🎵 TikTok видео", callback_data="submit_tiktok_video")
        )
    
    if has_youtube:
        builder.row(
            InlineKeyboardButton(text="📺 YouTube видео", callback_data="submit_youtube_video")
        )
    
    if not has_tiktok and not has_youtube:
        builder.row(
            InlineKeyboardButton(text="ℹ️ Сначала привяжите канал", callback_data="back_to_menu")
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def admin_keyboard() -> InlineKeyboardMarkup:
    """Админ панель"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Заявки на вывод", callback_data="admin_withdrawals")
    )
    builder.row(
        InlineKeyboardButton(text="🥉🥇 Управление статусами", callback_data="admin_tiers")
    )
    builder.row(
        InlineKeyboardButton(text="� Пополнить баланс", callback_data="admin_topup")
    )
    builder.row(
        InlineKeyboardButton(text="�📢 Рассылка", callback_data="admin_broadcast")
    )
    return builder.as_markup()


def video_moderation_keyboard(video_id: int) -> InlineKeyboardMarkup:
    """Кнопки модерации видео"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_video_{video_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_video_{video_id}")
    )
    return builder.as_markup()


def first_youtube_video_keyboard(video_id: int) -> InlineKeyboardMarkup:
    """Кнопки для первого YouTube видео - установить выплату"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Установить выплату", callback_data=f"set_rate_{video_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_video_{video_id}")
    )
    return builder.as_markup()


def withdrawal_action_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Действия с заявкой на вывод (для админа)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_withdrawal_{request_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_withdrawal_{request_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_withdrawals")
    )
    return builder.as_markup()


def admin_payout_keyboard(payout_id: int) -> InlineKeyboardMarkup:
    """Кнопки для админа - одобрить/отклонить выплату"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Выплатить", callback_data=f"approve_payout_{payout_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payout_{payout_id}")
    )
    return builder.as_markup()


def video_payout_keyboard(video_id: int) -> InlineKeyboardMarkup:
    """Кнопка запроса выплаты для видео"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Запросить выплату", callback_data=f"request_payout_{video_id}")
    )
    return builder.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Общая аналитика", callback_data="admin_analytics")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Топ пользователей", callback_data="admin_top_users"),
        InlineKeyboardButton(text="📹 Статистика видео", callback_data="admin_video_stats")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Управление юзерами", callback_data="admin_user_management"),
        InlineKeyboardButton(text="💰 Финансы", callback_data="admin_finances")
    )
    builder.row(
        InlineKeyboardButton(text="🎵 TikTok статистика", callback_data="admin_tiktok_stats"),
        InlineKeyboardButton(text="📺 YouTube статистика", callback_data="admin_youtube_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🔑 Выдача ключей", callback_data="admin_media_keys")
    )
    return builder.as_markup()


def admin_time_filter_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора временного периода"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Сегодня", callback_data=f"{action}_today"),
        InlineKeyboardButton(text="📅 Вчера", callback_data=f"{action}_yesterday")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data=f"{action}_week"),
        InlineKeyboardButton(text="📅 Месяц", callback_data=f"{action}_month")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Всё время", callback_data=f"{action}_all")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )
    return builder.as_markup()


def admin_user_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Действия с пользователем"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚫 Забанить", callback_data=f"admin_ban_{user_id}"),
        InlineKeyboardButton(text="✅ Разбанить", callback_data=f"admin_unban_{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💸 Обнулить баланс", callback_data=f"admin_reset_balance_{user_id}"),
        InlineKeyboardButton(text="🥇 Изменить тир", callback_data=f"admin_change_tier_{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_user_stats_{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_user_management")
    )
    return builder.as_markup()


def admin_media_keys_keyboard() -> InlineKeyboardMarkup:
    """Меню управления ключами"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Загрузить ключи", callback_data="admin_media_keys_upload"),
        InlineKeyboardButton(text="📄 Последние выдачи", callback_data="admin_media_keys_recent")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )
    return builder.as_markup()


def cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Клавиатура отмены с настраиваемым callback"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=callback_data)
    )
    return builder.as_markup()
