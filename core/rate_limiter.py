"""
Rate Limiting Middleware для защиты от спама и DDoS атак
"""
import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов от пользователей
    
    Args:
        rate_limit: Минимальное время между сообщениями (в секундах)
        max_requests: Максимальное количество запросов в период
        period: Период времени для подсчета запросов (в секундах)
    """
    
    def __init__(
        self,
        rate_limit: float = 1.0,  # 1 секунда между сообщениями
        max_requests: int = 10,    # 10 запросов
        period: int = 60           # за 60 секунд
    ):
        self.rate_limit = rate_limit
        self.max_requests = max_requests
        self.period = period
        
        # Хранение последнего времени запроса для каждого пользователя
        self.last_request_time: Dict[int, float] = {}
        
        # Хранение истории запросов для подсчета
        self.request_history: Dict[int, list] = {}
        
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка входящего события"""
        
        # Получаем пользователя из события
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        
        # Если пользователя нет, пропускаем проверку
        if not user:
            return await handler(event, data)
        
        user_id = user.id
        current_time = time.time()
        
        # Проверка 1: Простой rate limit (минимальное время между запросами)
        if user_id in self.last_request_time:
            time_passed = current_time - self.last_request_time[user_id]
            
            if time_passed < self.rate_limit:
                # Слишком быстро!
                logger.warning(f"Rate limit exceeded for user {user_id} ({user.username})")
                
                if event.message:
                    await event.message.answer(
                        "⚠️ Слишком много запросов. Пожалуйста, подождите немного.",
                        show_alert=True
                    )
                elif event.callback_query:
                    await event.callback_query.answer(
                        "⚠️ Слишком быстро! Подождите немного.",
                        show_alert=True
                    )
                
                return  # Блокируем запрос
        
        # Проверка 2: Максимальное количество запросов за период
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        # Очищаем старые запросы (старше period секунд)
        self.request_history[user_id] = [
            req_time for req_time in self.request_history[user_id]
            if current_time - req_time < self.period
        ]
        
        # Проверяем количество запросов
        if len(self.request_history[user_id]) >= self.max_requests:
            logger.warning(
                f"Too many requests from user {user_id} ({user.username}): "
                f"{len(self.request_history[user_id])} requests in {self.period}s"
            )
            
            if event.message:
                await event.message.answer(
                    f"⚠️ Превышен лимит запросов!\n"
                    f"Максимум {self.max_requests} запросов за {self.period} секунд.\n"
                    f"Пожалуйста, подождите немного."
                )
            elif event.callback_query:
                await event.callback_query.answer(
                    f"⚠️ Превышен лимит запросов! Подождите {self.period}с",
                    show_alert=True
                )
            
            return  # Блокируем запрос
        
        # Сохраняем время запроса
        self.last_request_time[user_id] = current_time
        self.request_history[user_id].append(current_time)
        
        # Пропускаем запрос дальше
        return await handler(event, data)
    
    def reset_user(self, user_id: int):
        """Сброс лимитов для пользователя (для админских действий)"""
        if user_id in self.last_request_time:
            del self.last_request_time[user_id]
        if user_id in self.request_history:
            del self.request_history[user_id]
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику запросов пользователя"""
        return {
            "last_request": self.last_request_time.get(user_id),
            "requests_count": len(self.request_history.get(user_id, [])),
            "max_requests": self.max_requests,
            "period": self.period
        }


class AdminRateLimitMiddleware(RateLimitMiddleware):
    """
    Более мягкий rate limiter для администраторов
    """
    
    def __init__(self, admin_ids: list):
        self.admin_ids = admin_ids
        # Ограничения для обычных пользователей (админы освобождены)
        super().__init__(
            rate_limit=0.5,    # 0.5 секунды между запросами
            max_requests=30,   # 30 запросов
            period=60          # за 60 секунд
        )
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка с учетом админских прав"""
        
        # Получаем пользователя
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        
        # Если пользователь админ, пропускаем проверки
        if user and user.id in self.admin_ids:
            return await handler(event, data)
        
        # Для обычных пользователей применяем стандартные проверки
        return await super().__call__(handler, event, data)
