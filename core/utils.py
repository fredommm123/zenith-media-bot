import re
from typing import Optional


def format_number(number: float, decimals: int = 2) -> str:
    """Форматировать число"""
    return f"{number:,.{decimals}f}".replace(",", " ")


def format_currency(amount: float) -> str:
    """Форматировать валюту"""
    return f"{format_number(amount, 2)} ₽"


def validate_channel_id(channel_id: str) -> bool:
    """Проверить формат ID канала"""
    # Должен начинаться с @ или быть числом
    if channel_id.startswith("@"):
        return len(channel_id) > 1
    try:
        int(channel_id)
        return True
    except ValueError:
        return False


def validate_card_number(card_number: str) -> bool:
    """Проверить формат номера карты"""
    # Удаляем пробелы
    card_number = card_number.replace(" ", "")
    # Проверяем, что это 16 цифр
    return bool(re.match(r'^\d{16}$', card_number))


def validate_phone_number(phone: str) -> bool:
    """Проверить формат номера телефона"""
    # Удаляем все кроме цифр и +
    phone = re.sub(r'[^\d+]', '', phone)
    # Проверяем формат российского номера
    return bool(re.match(r'^\+?[78]?\d{10}$', phone))


def format_card_number(card_number: str) -> str:
    """Форматировать номер карты (скрыть средние цифры)"""
    card_number = card_number.replace(" ", "")
    if len(card_number) == 16:
        return f"{card_number[:4]} **** **** {card_number[-4:]}"
    return card_number


def format_phone_number(phone: str) -> str:
    """Форматировать номер телефона (скрыть средние цифры)"""
    phone = re.sub(r'[^\d+]', '', phone)
    if len(phone) >= 11:
        return f"+{phone[0]}***{phone[-4:]}"
    return phone


def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Генерировать реферальную ссылку"""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def parse_referral_code(start_param: Optional[str]) -> Optional[int]:
    """Парсить реферальный код из параметра start"""
    if not start_param:
        return None
    
    if start_param.startswith("ref_"):
        try:
            return int(start_param[4:])
        except ValueError:
            return None
    
    return None


def calculate_pages(total_items: int, items_per_page: int = 10) -> int:
    """Рассчитать количество страниц"""
    return max(1, (total_items + items_per_page - 1) // items_per_page)


def escape_markdown(text: str) -> str:
    """Экранировать специальные символы для Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_timestamp(timestamp: str) -> str:
    """Форматировать timestamp"""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return timestamp


def get_status_emoji(status: str) -> str:
    """Получить эмодзи для статуса"""
    status_emojis = {
        "pending": "⏳",
        "processing": "🔄",
        "completed": "✅",
        "rejected": "❌",
        "approved": "✅"
    }
    return status_emojis.get(status, "❓")


def get_status_text(status: str) -> str:
    """Получить текст статуса"""
    status_texts = {
        "pending": "Ожидает",
        "processing": "Обрабатывается",
        "completed": "Завершено",
        "rejected": "Отклонено",
        "approved": "Одобрено"
    }
    return status_texts.get(status, "Неизвестно")


async def send_to_admin_chat(bot, text: str, reply_markup=None, parse_mode="HTML", edit_message_id=None):
    """Отправить или обновить сообщение в админ-чате"""
    from core import config
    
    # Отправляем в админ-чат если указан
    if config.ADMIN_CHAT_ID:
        try:
            if edit_message_id:
                # Редактируем существующее сообщение
                return await bot.edit_message_text(
                    text,
                    chat_id=config.ADMIN_CHAT_ID,
                    message_id=edit_message_id,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                # Отправляем новое сообщение
                return await bot.send_message(
                    config.ADMIN_CHAT_ID,
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e:
            print(f"Ошибка отправки в админ-чат: {e}")
            return None
    
    # Если админ-чат не указан, отправляем всем админам
    for admin_id in config.ADMIN_IDS:
        try:
            if edit_message_id:
                await bot.edit_message_text(
                    text,
                    chat_id=admin_id,
                    message_id=edit_message_id,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                await bot.send_message(
                    admin_id,
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")
    
    return None
