# Система накопления баланса и автоматических выплат

## 📝 Описание функции

Реализована система накопления средств на балансе пользователя с автоматическими выплатами при достижении минимального порога.

---

## 🎯 Как это работает

### 1. Видео с доходом < 1 USDT
- **Деньги зачисляются на баланс** пользователя
- Пользователь видит уведомление о зачислении
- Показывается текущий баланс и сколько осталось накопить до 1 USDT

### 2. Видео с доходом ≥ 1 USDT
- Пользователю отправляется **кнопка "Запросить выплату"**
- При нажатии деньги **автоматически** отправляются через Crypto Bot

### 3. Вывод накопленного баланса
- Когда баланс ≥ 1 USDT → в профиле появляется кнопка **"💸 Запросить выплату"**
- При нажатии:
  - Баланс автоматически выводится через Crypto Bot
  - Баланс обнуляется
  - Сумма добавляется к `total_withdrawn`

---

## 💻 Технические детали

### Измененные файлы:

#### 1. `handlers/admin.py`
**Функция:** `approve_video()`

**Логика:**
```python
# Рассчитываем выплату за видео
payout_amount = await calculate_payout_amount(views, platform, user_id, video_id)

# Конвертируем в USDT
rate = await get_exchange_rate_rub_to_usdt()
usdt_amount = payout_amount / rate

if usdt_amount < 1.0:
    # ✅ Зачисляем на баланс
    await db.update_user_balance(user_id, payout_amount, operation='add')
    
    # Показываем сколько осталось накопить
    new_balance_usdt = new_balance / rate
    if new_balance_usdt >= 1.0:
        # Можно вывести!
        message += "✅ Вы можете вывести деньги!"
    else:
        needed_rub = (1.0 - new_balance_usdt) * rate
        message += f"Осталось накопить: ~{needed_rub:.2f} ₽"
else:
    # ✅ Отправляем кнопку выплаты
    # Пользователь нажмет → деньги сразу улетят
```

---

#### 2. `handlers/payouts.py`
**Новая функция:** `request_balance_payout_callback()`

**Что делает:**
1. Проверяет баланс пользователя
2. Конвертирует в USDT
3. Проверяет минимум (1 USDT)
4. Отправляет платеж через Crypto Bot
5. Обнуляет баланс при успехе
6. Обновляет `total_withdrawn`

**Код:**
```python
@router.callback_query(F.data == "request_balance_payout")
async def request_balance_payout_callback(callback: CallbackQuery):
    user = await db.get_user(user_id)
    balance = user['balance']
    
    # Проверяем минимум
    usdt_amount = balance / rate
    if usdt_amount < 1.0:
        await callback.answer("❌ Минимум 1 USDT")
        return
    
    # Отправляем выплату
    payment_result = await send_payment(...)
    
    if payment_result['success']:
        # Обнуляем баланс
        await db.update_user_balance(user_id, 0, operation='set')
        
        # Обновляем статистику
        await db.update_user_stats_withdrawal(user_id, balance)
```

---

#### 3. `core/database.py`
**Новые/измененные функции:**

1. **`update_user_balance()`** - расширена:
```python
async def update_user_balance(self, user_id: int, amount: float, operation: str = 'add'):
    """
    operation: 'add' | 'subtract' | 'set'
    """
    if operation == 'add':
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", ...)
    elif operation == 'subtract':
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", ...)
    elif operation == 'set':
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", ...)
```

2. **`update_user_stats_withdrawal()`** - новая:
```python
async def update_user_stats_withdrawal(self, user_id: int, amount: float):
    """Обновляет total_withdrawn"""
    await db.execute(
        "UPDATE users SET total_withdrawn = total_withdrawn + ? WHERE user_id = ?",
        (amount, user_id)
    )
```

---

#### 4. `core/keyboards.py`
**Изменение:** Добавлен параметр `balance` в `profile_keyboard()`

```python
def profile_keyboard(has_tiktok: bool = False, has_youtube: bool = False, balance: float = 0):
    builder = InlineKeyboardBuilder()
    
    # ... другие кнопки ...
    
    # Показываем кнопку "Запросить выплату" если баланс > 0
    if balance > 0:
        builder.row(
            InlineKeyboardButton(text="💸 Запросить выплату", callback_data="request_balance_payout")
        )
    
    return builder.as_markup()
```

---

#### 5. `handlers/profile.py`
**Изменение:** Передаем баланс в клавиатуру

```python
await message.answer(
    profile_text, 
    reply_markup=profile_keyboard(
        has_tiktok=bool(tiktok), 
        has_youtube=bool(youtube), 
        balance=user['balance']  # ✅ Передаем баланс
    )
)
```

---

## 📊 Пример работы

### Сценарий 1: Малый доход (< 1 USDT)

**Видео:** 500 просмотров TikTok

**Расчет:**
- Ставка: 65₽ / 1000 просмотров
- Доход: (500 / 1000) × 65 = **32.5₽**
- В USDT: 32.5 / 95 ≈ **0.34 USDT** ❌ < 1 USDT

**Результат:**
```
✅ Ваше видео одобрено!

💰 Начислено: 32.5 ₽ (~0.3421 USDT)

💳 Деньги зачислены на ваш баланс!
💰 Текущий баланс: 32.5 ₽ (~0.3421 USDT)

ℹ️ Минимум для вывода: 1 USDT
Осталось накопить: ~62.50 ₽
```

---

### Сценарий 2: Накопление на балансе

**Видео 1:** 32.5₽ → Баланс: 32.5₽ (0.34 USDT)  
**Видео 2:** 45₽ → Баланс: 77.5₽ (0.82 USDT)  
**Видео 3:** 25₽ → Баланс: 102.5₽ (1.08 USDT) ✅

**Результат после видео 3:**
```
✅ Ваше видео одобрено!

💰 Начислено: 25 ₽ (~0.2632 USDT)

💳 Деньги зачислены на ваш баланс!
💰 Текущий баланс: 102.5 ₽ (~1.0789 USDT)

✅ Вы можете вывести деньги!
Используйте команду /profile → 💸 Запросить выплату
```

**В профиле появляется кнопка:**
```
[💸 Запросить выплату]
```

**При нажатии:**
```
✅ Выплата успешно отправлена!

💰 Сумма: 102.5 ₽
💵 В USDT: 1.078947 USDT

💳 Выплачено с баланса аккаунта
💼 Новый баланс: 0.00 ₽

🎉 Деньги отправлены на ваш @CryptoBot аккаунт!
```

---

### Сценарий 3: Большой доход (≥ 1 USDT)

**Видео:** 2000 просмотров TikTok

**Расчет:**
- Доход: (2000 / 1000) × 65 = **130₽**
- В USDT: 130 / 95 ≈ **1.37 USDT** ✅ ≥ 1 USDT

**Результат:**
```
✅ Ваше видео одобрено!

💰 Выплата: 130 ₽ (~1.3684 USDT)

⬇️ Нажмите кнопку ниже для получения выплаты:
[💰 Запросить выплату]
```

**При нажатии кнопки:**
```
⏳ Отправка выплаты...

✅ Выплата успешно отправлена!

💰 Сумма: 130.00 ₽
💵 В USDT: 1.368421 USDT

📊 Видео ID: 123
👁 Просмотров: 2,000

🎉 Деньги отправлены на ваш @CryptoBot аккаунт!
```

---

## ✅ Преимущества системы

1. **Не теряются маленькие суммы** - все копится на балансе
2. **Автоматические выплаты** - пользователю не нужно ждать админа
3. **Прозрачность** - видно сколько накоплено и сколько осталось
4. **Меньше транзакций** - Crypto Bot берет комиссию, лучше выводить крупными суммами

---

## 🔗 Ссылки

- **GitHub:** https://github.com/fredommm123/zenith-media-bot
- **Коммит:** d731242 "Система накопления баланса"
- **VDS:** 185.176.94.108 (/zenithmedia_bot)
- **Статус:** ✅ Развернуто и работает

---

## 📞 Поддержка

При возникновении проблем проверьте:
1. Логи: `journalctl -u zenithmedia-bot -n 50`
2. Баланс Crypto Bot: должно быть ≥ 1 USDT
3. Username пользователя: должен быть установлен в Telegram
