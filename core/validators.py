"""
Модуль для валидации входных данных
Защита от SQL инъекций, XSS и других атак
"""
import re
from typing import Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Ошибка валидации"""
    pass


class Validators:
    """Класс с методами валидации различных типов данных"""
    
    @staticmethod
    def validate_tiktok_url(url: str) -> str:
        """
        Валидация TikTok URL
        
        Args:
            url: URL для проверки
            
        Returns:
            str: Валидированный URL
            
        Raises:
            ValidationError: Если URL невалиден
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL не может быть пустым")
        
        url = url.strip()
        
        # Проверка длины
        if len(url) > 500:
            raise ValidationError("URL слишком длинный")
        
        # Проверка формата
        patterns = [
            r'^https?://(www\.)?tiktok\.com/@[^/]+/video/\d+',
            r'^https?://(vm|vt)\.tiktok\.com/[A-Za-z0-9]+',
        ]
        
        if not any(re.match(pattern, url) for pattern in patterns):
            raise ValidationError(
                "Неверный формат TikTok URL. "
                "Используйте ссылки вида: "
                "https://www.tiktok.com/@username/video/123456789"
            )
        
        # Проверка на вредоносные символы
        if any(char in url for char in ['<', '>', '"', "'", ';', '(', ')']):
            raise ValidationError("URL содержит недопустимые символы")
        
        return url
    
    @staticmethod
    def validate_youtube_url(url: str) -> str:
        """
        Валидация YouTube URL (видео или канал)
        
        Args:
            url: URL для проверки
            
        Returns:
            str: Валидированный URL
            
        Raises:
            ValidationError: Если URL невалиден
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL не может быть пустым")
        
        url = url.strip()
        
        # Проверка длины
        if len(url) > 500:
            raise ValidationError("URL слишком длинный")
        
        # Проверка формата (канал или видео)
        patterns = [
            r'^https?://(www\.)?youtube\.com/@[\w-]+',
            r'^https?://(www\.)?youtube\.com/c/[\w-]+',
            r'^https?://(www\.)?youtube\.com/channel/UC[\w-]+',
            r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://youtu\.be/[\w-]+',
        ]
        
        if not any(re.match(pattern, url) for pattern in patterns):
            raise ValidationError(
                "Неверный формат YouTube URL. "
                "Используйте ссылки на канал или видео"
            )
        
        # Проверка на вредоносные символы
        if any(char in url for char in ['<', '>', '"', "'", ';']):
            raise ValidationError("URL содержит недопустимые символы")
        
        return url
    
    @staticmethod
    def validate_amount(amount: Union[str, int, float], 
                       min_value: float = 0.0, 
                       max_value: float = 1000000.0) -> float:
        """
        Валидация денежной суммы
        
        Args:
            amount: Сумма для проверки
            min_value: Минимальное значение
            max_value: Максимальное значение
            
        Returns:
            float: Валидированная сумма
            
        Raises:
            ValidationError: Если сумма невалидна
        """
        try:
            # Преобразуем в число
            if isinstance(amount, str):
                # Убираем пробелы и заменяем запятую на точку
                amount = amount.strip().replace(',', '.').replace(' ', '')
            
            value = float(amount)
            
            # Проверка диапазона
            if value < min_value:
                raise ValidationError(f"Сумма не может быть меньше {min_value}")
            
            if value > max_value:
                raise ValidationError(f"Сумма не может быть больше {max_value}")
            
            # Проверка на NaN и Infinity
            if not (value == value):  # NaN check
                raise ValidationError("Некорректное значение суммы")
            
            if value == float('inf') or value == float('-inf'):
                raise ValidationError("Некорректное значение суммы")
            
            # Округляем до 2 знаков после запятой
            return round(value, 2)
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Некорректный формат суммы: {str(e)}")
    
    @staticmethod
    def validate_user_id(user_id: Union[str, int]) -> int:
        """
        Валидация Telegram User ID
        
        Args:
            user_id: ID для проверки
            
        Returns:
            int: Валидированный ID
            
        Raises:
            ValidationError: Если ID невалиден
        """
        try:
            user_id_int = int(user_id)
            
            # Telegram user ID всегда положительный и не превышает определенного значения
            if user_id_int <= 0 or user_id_int > 9999999999:
                raise ValidationError("Некорректный User ID")
            
            return user_id_int
            
        except (ValueError, TypeError):
            raise ValidationError("User ID должен быть числом")
    
    @staticmethod
    def validate_text_input(text: str, 
                           max_length: int = 1000,
                           allow_newlines: bool = True,
                           field_name: str = "Текст") -> str:
        """
        Валидация текстового ввода
        
        Args:
            text: Текст для проверки
            max_length: Максимальная длина
            allow_newlines: Разрешены ли переносы строк
            field_name: Название поля для сообщения об ошибке
            
        Returns:
            str: Валидированный текст
            
        Raises:
            ValidationError: Если текст невалиден
        """
        if not text:
            raise ValidationError(f"{field_name} не может быть пустым")
        
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} должен быть строкой")
        
        text = text.strip()
        
        # Проверка длины
        if len(text) > max_length:
            raise ValidationError(
                f"{field_name} слишком длинный (максимум {max_length} символов)"
            )
        
        # Проверка на переносы строк
        if not allow_newlines and '\n' in text:
            raise ValidationError(f"{field_name} не может содержать переносы строк")
        
        # Проверка на опасные символы (защита от XSS)
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
            r'<iframe',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                logger.warning(f"Detected potentially dangerous input: {pattern}")
                raise ValidationError(f"{field_name} содержит недопустимые элементы")
        
        return text
    
    @staticmethod
    def validate_username(username: str) -> str:
        """
        Валидация Telegram username
        
        Args:
            username: Username для проверки
            
        Returns:
            str: Валидированный username
            
        Raises:
            ValidationError: Если username невалиден
        """
        if not username:
            raise ValidationError("Username не может быть пустым")
        
        # Убираем @ если есть
        username = username.lstrip('@').strip()
        
        # Проверка формата (только буквы, цифры и подчеркивания)
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
            raise ValidationError(
                "Username должен содержать от 5 до 32 символов "
                "(только буквы, цифры и подчеркивания)"
            )
        
        return username
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Очистка строки для безопасного использования в SQL
        ВАЖНО: Это НЕ замена параметризованных запросов!
        Используйте только как дополнительную защиту
        
        Args:
            value: Значение для очистки
            
        Returns:
            str: Очищенное значение
        """
        if not isinstance(value, str):
            return value
        
        # Удаляем опасные символы
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def validate_rate(rate: Union[str, int, float]) -> float:
        """
        Валидация ставки за 1000 просмотров
        
        Args:
            rate: Ставка для проверки
            
        Returns:
            float: Валидированная ставка
            
        Raises:
            ValidationError: Если ставка невалидна
        """
        try:
            rate_value = Validators.validate_amount(
                rate,
                min_value=1.0,    # Минимум 1 рубль
                max_value=500.0   # Максимум 500 рублей
            )
            return rate_value
        except ValidationError:
            raise ValidationError(
                "Ставка должна быть от 1 до 500 рублей за 1000 просмотров"
            )


# Удобные функции для быстрой валидации
def validate_tiktok_url(url: str) -> str:
    """Быстрая валидация TikTok URL"""
    return Validators.validate_tiktok_url(url)


def validate_youtube_url(url: str) -> str:
    """Быстрая валидация YouTube URL"""
    return Validators.validate_youtube_url(url)


def validate_amount(amount: Union[str, int, float], 
                   min_value: float = 0.0, 
                   max_value: float = 1000000.0) -> float:
    """Быстрая валидация суммы"""
    return Validators.validate_amount(amount, min_value, max_value)


def validate_user_id(user_id: Union[str, int]) -> int:
    """Быстрая валидация User ID"""
    return Validators.validate_user_id(user_id)
