"""
Модуль для работы с Crypto Bot API
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.transfer import Transfer
from aiocryptopay.models.invoice import Invoice
from core.config import CRYPTO_PAY_TOKEN, CRYPTO_PAY_TESTNET

logger = logging.getLogger(__name__)

# Инициализация Crypto Pay клиента
crypto = AioCryptoPay(
    token=CRYPTO_PAY_TOKEN,
    network=Networks.TEST_NET if CRYPTO_PAY_TESTNET else Networks.MAIN_NET
)


async def get_exchange_rate_rub_to_usdt() -> Optional[float]:
    """
    Получить курс RUB -> USDT
    
    Returns:
        float: Курс (сколько USDT за 1 RUB) или None при ошибке
    """
    try:
        rates = await crypto.get_exchange_rates()
        
        # Ищем курс USDT -> RUB
        for rate in rates:
            if rate.source == "USDT" and rate.target == "RUB":
                # Если 1 USDT = 95 RUB, то 1 RUB = 1/95 USDT
                usdt_per_rub = 1.0 / float(rate.rate)
                logger.info(f"Текущий курс: 1 RUB = {usdt_per_rub:.6f} USDT (1 USDT = {rate.rate} RUB)")
                return usdt_per_rub
        
        logger.error("Не найден курс USDT -> RUB")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка получения курса валют: {e}")
        return None


async def calculate_usdt_amount(rub_amount: float) -> Optional[float]:
    """
    Конвертировать рубли в USDT
    
    Args:
        rub_amount: Сумма в рублях
        
    Returns:
        float: Сумма в USDT или None при ошибке
    """
    rate = await get_exchange_rate_rub_to_usdt()
    if rate is None:
        return None
    
    usdt_amount = rub_amount * rate
    logger.info(f"Конвертация: {rub_amount} RUB = {usdt_amount:.6f} USDT")
    return usdt_amount


async def send_payment(
    user_id: int,
    amount_rub: float,
    spend_id: str,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Отправить USDT пользователю через Crypto Bot
    
    Args:
        user_id: Telegram ID пользователя
        amount_rub: Сумма в рублях
        spend_id: Уникальный ID транзакции (для идемпотентности)
        comment: Комментарий к переводу
        
    Returns:
        dict: {"success": bool, "transfer": Transfer or None, "error": str or None}
    """
    try:
        # Конвертируем рубли в USDT
        usdt_amount = await calculate_usdt_amount(amount_rub)
        
        if usdt_amount is None:
            return {
                "success": False,
                "transfer": None,
                "error": "Не удалось получить курс валют"
            }
        
        # Минимальная сумма перевода ~1 USD
        if usdt_amount < 1.0:
            return {
                "success": False,
                "transfer": None,
                "error": f"Сумма перевода слишком мала ({usdt_amount:.2f} USDT). Минимум ~1 USDT"
            }
        
        # Проверяем баланс перед отправкой
        app_balance = await get_app_balance()
        if app_balance and app_balance.get('USDT', 0) < usdt_amount:
            return {
                "success": False,
                "transfer": None,
                "error": f"Недостаточно USDT на балансе приложения. Нужно: {usdt_amount:.2f}, Доступно: {app_balance.get('USDT', 0):.2f}"
            }
        
        # Отправляем перевод
        logger.info(f"Отправка {usdt_amount:.6f} USDT (≈{amount_rub} RUB) пользователю {user_id}")
        
        try:
            transfer = await crypto.transfer(
                user_id=user_id,
                asset="USDT",
                amount=usdt_amount,
                spend_id=spend_id,
                disable_send_notification=False
                # comment не поддерживается - убираем его
            )
            
            logger.info(f"✅ Перевод успешен! Transfer ID: {transfer.transfer_id}")
            
            return {
                "success": True,
                "transfer": transfer,
                "error": None,
                "usdt_amount": usdt_amount
            }
        
        except Exception as transfer_error:
            error_msg = str(transfer_error)
            logger.error(f"Ошибка transfer(): {error_msg}")
            
            # Детальная обработка ошибок
            if "403" in error_msg or "METHOD_DISABLED" in error_msg:
                return {
                    "success": False,
                    "transfer": None,
                    "error": "⚠️ Метод отправки отключен в @CryptoBot.\n\n" +
                            "Инструкция:\n" +
                            "1. Открой @CryptoBot\n" +
                            "2. Настройки → My Apps → выбери приложение\n" +
                            "3. Включи 'Allow Transfers'\n" +
                            "4. Пополни баланс приложения"
                }
            elif "CANNOT_ATTACH_COMMENT" in error_msg:
                return {
                    "success": False,
                    "transfer": None,
                    "error": "❌ Ошибка: Crypto Bot не поддерживает комментарии к переводам"
                }
            elif "USER_NOT_FOUND" in error_msg:
                return {
                    "success": False,
                    "transfer": None,
                    "error": f"❌ Пользователь {user_id} не найден в @CryptoBot.\nПопросите пользователя запустить @CryptoBot"
                }
            elif "INSUFFICIENT_FUNDS" in error_msg:
                return {
                    "success": False,
                    "transfer": None,
                    "error": f"❌ Недостаточно USDT на балансе приложения ({app_balance.get('USDT', 0):.2f} USDT)"
                }
            else:
                return {
                    "success": False,
                    "transfer": None,
                    "error": f"❌ Ошибка Crypto Bot: {error_msg}"
                }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Общая ошибка отправки платежа: {error_msg}")
        
        return {
            "success": False,
            "transfer": None,
            "error": f"❌ Неожиданная ошибка: {error_msg}"
        }


async def get_app_balance() -> Optional[Dict[str, float]]:
    """
    Получить баланс приложения
    
    Returns:
        dict: {"USDT": available, "TON": available, ...} или None при ошибке
    """
    try:
        balances = await crypto.get_balance()
        
        balance_dict = {}
        for balance in balances:
            balance_dict[balance.currency_code] = float(balance.available)
        
        logger.info(f"Баланс приложения: {balance_dict}")
        return balance_dict
        
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return None


async def check_transfer_settings() -> dict:
    """
    Проверяет настройки приложения и возможность отправки переводов
    
    Returns:
        dict: Информация о настройках и доступности переводов
    """
    try:
        # Получаем информацию о приложении
        me = await crypto.get_me()
        balance = await get_app_balance()
        
        info = {
            "app_id": me.app_id,
            "name": me.name,
            "payment_processing_bot_username": me.payment_processing_bot_username,
            "balance": balance or {},
            "usdt_balance": (balance or {}).get('USDT', 0),
            "has_balance": (balance or {}).get('USDT', 0) > 0,
            "errors": []
        }
        
        # Проверки
        if info["usdt_balance"] == 0:
            info["errors"].append("⚠️ Баланс USDT = 0. Пополните баланс приложения в @CryptoBot")
        
        logger.info(f"Проверка настроек: {info}")
        return info
        
    except Exception as e:
        logger.error(f"Ошибка проверки настроек: {e}")
        return {
            "errors": [f"❌ Ошибка подключения к Crypto Bot: {str(e)}"]
        }


async def test_crypto_connection() -> bool:
    """
    Проверить подключение к Crypto Bot API
    
    Returns:
        bool: True если успешно
    """
    try:
        app = await crypto.get_me()
        logger.info(f"✅ Подключение к Crypto Bot API успешно!")
        logger.info(f"   Приложение: {app.name}")
        logger.info(f"   App ID: {app.app_id}")
        
        # Проверяем баланс
        balances = await get_app_balance()
        if balances:
            logger.info(f"   Балансы: {balances}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Crypto Bot API: {e}")
        return False


async def create_invoice(amount: float, currency: str = "USDT", description: str = None) -> Optional[Dict[str, Any]]:
    """
    Создать счет для пополнения баланса приложения
    
    Args:
        amount: Сумма в указанной валюте
        currency: Валюта (USDT, TON, BTC, ETH и т.д.)
        description: Описание платежа
    
    Returns:
        dict: Информация о счете (invoice_id, bot_invoice_url, mini_app_invoice_url) или None
    """
    try:
        # Создаем счет
        invoice = await crypto.create_invoice(
            asset=currency,
            amount=amount,
            description=description or f"Пополнение баланса Zenith Media: {amount} {currency}"
            # Не указываем paid_btn_name и paid_btn_url - они не обязательны
        )
        
        logger.info(f"✅ Счет создан: {amount} {currency}")
        logger.info(f"   Invoice ID: {invoice.invoice_id}")
        logger.info(f"   Bot URL: {invoice.bot_invoice_url}")
        
        return {
            "success": True,
            "invoice_id": invoice.invoice_id,
            "bot_invoice_url": invoice.bot_invoice_url,
            "mini_app_invoice_url": invoice.mini_app_invoice_url,
            "amount": amount,
            "currency": currency,
            "status": invoice.status,
            "created_at": invoice.created_at,
            "error": None
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка создания счета: {error_msg}")
        
        return {
            "success": False,
            "invoice_id": None,
            "bot_invoice_url": None,
            "mini_app_invoice_url": None,
            "error": f"❌ Ошибка создания счета: {error_msg}"
        }


async def get_invoice_status(invoice_id: int) -> Optional[Dict[str, Any]]:
    """
    Проверить статус счета
    
    Args:
        invoice_id: ID счета
    
    Returns:
        dict: Информация о статусе счета
    """
    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        
        if not invoices or len(invoices) == 0:
            return {
                "success": False,
                "status": "not_found",
                "error": "Счет не найден"
            }
        
        invoice = invoices[0]
        
        logger.info(f"Статус счета {invoice_id}: {invoice.status}")
        
        return {
            "success": True,
            "invoice_id": invoice.invoice_id,
            "status": invoice.status,  # active, paid, expired
            "amount": float(invoice.amount),
            "currency": invoice.asset,
            "paid_at": invoice.paid_at,
            "error": None
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка проверки статуса счета: {error_msg}")
        
        return {
            "success": False,
            "status": "error",
            "error": f"❌ Ошибка: {error_msg}"
        }


async def close_crypto_session():
    """Закрыть сессию Crypto Pay"""
    try:
        await crypto.close()
        logger.info("Сессия Crypto Pay закрыта")
    except Exception as e:
        logger.error(f"Ошибка закрытия сессии Crypto Pay: {e}")
