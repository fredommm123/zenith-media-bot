# 🎬 ZenithMedia Bot# ZenithMedia Bot



Telegram бот для монетизации контента с TikTok и YouTube. Автоматические выплаты через Crypto Bot API с системой уровней (Bronze/Gold).Telegram бот для монетизации видеоконтента TikTok и YouTube с автоматическими выплатами через Crypto Pay.



## 🌟 Возможности## 🚀 Возможности



### Для пользователей### Основные функции

- 📱 **TikTok интеграция** - Загрузка видео и автоматический подсчет просмотров- ✅ Регистрация и управление профилем

- 🎥 **YouTube интеграция** - Привязка канала и фиксированная оплата за видео- 🎵 Привязка TikTok аккаунтов с автоматической верификацией

- 💰 **Автоматические выплаты** - Моментальные выплаты для Gold пользователей- 📺 Привязка YouTube каналов с кодом верификации

- 🥇 **Система уровней** - Bronze (проверка 24ч) и Gold (моментально)- 🎬 Подача видео на монетизацию (TikTok и YouTube)

- 👥 **Реферальная программа** - 10% от заработка рефералов- 💰 Автоматические выплаты в USDT через Crypto Bot

- 💳 **Crypto Bot выплаты** - Безопасные выплаты в USDT через @CryptoBot- 📊 Парсинг статистики видео (просмотры, лайки, комментарии)

- 📜 История видео и выплат

### Для администраторов

- ⚙️ **Админ-панель** - Полный контроль через Telegram### Система уровней 🆕

- 📊 **Гибкие ставки** - Индивидуальная ставка для каждого YouTube канала- 🥉 **Bronze** - вывод через 24 часа (по умолчанию)

- 🎯 **Управление уровнями** - Повышение/понижение пользователей- 🥇 **Gold** - моментальный вывод средств

- 💸 **Пополнение баланса** - Создание счетов через Crypto Bot

- 📈 **Статистика** - Отслеживание всех операций### Монетизация

- **TikTok**: 65₽ за 1000 просмотров (фиксированная ставка)

## 🚀 Быстрый старт- **YouTube**: индивидуальная ставка для каждого канала



### Требования### Реферальная программа

- 👥 10% от заработка рефералов

- Python 3.11+- � Уникальная реферальная ссылка для каждого пользователя

- SQLite3

- ffmpeg### Админ-панель 👑

- Telegram Bot Token- 📊 Статистика бота

- Crypto Bot API Token- ✅ Модерация видео

- 💰 Одобрение выплат с автоматической отправкой USDT

### Установка (Windows)- 🎯 Установка индивидуальных ставок для YouTube

- 🥉🥇 Управление уровнями пользователей

```bash

# Клонировать репозиторий## 📋 Требования

git clone https://github.com/yourusername/zenithmedia_bot.git

cd zenithmedia_bot- Python 3.9+

- SQLite3

# Создать виртуальное окружение

python -m venv venv## 🛠️ Установка

venv\Scripts\activate

1. Клонируйте репозиторий:

# Установить зависимости```bash

pip install -r requirements.txtgit clone <repository-url>

cd zenithmedia_bot

# Настроить конфигурацию```

copy .env.example .env

# Отредактируйте .env своими данными2. Установите зависимости:

```bash

# Запустить ботаpip install -r requirements.txt

python bot.py```

```

3. Создайте файл `.env` на основе `.env.example`:

### Установка (Linux/Ubuntu VDS)```bash

cp .env.example .env

```bash```

# Клонировать репозиторий

git clone https://github.com/yourusername/zenithmedia_bot.git4. Отредактируйте `.env` и добавьте ваш токен бота:

cd zenithmedia_bot```env

BOT_TOKEN=your_bot_token_here

# Запустить автоматическую установкуADMIN_IDS=123456789,987654321

chmod +x setup_vds.shMIN_WITHDRAWAL=100

sudo ./setup_vds.shREFERRAL_PERCENT=10

```

# Управление ботом

./bot_control.sh start    # Запустить## 🚀 Запуск

./bot_control.sh stop     # Остановить

./bot_control.sh logs     # Смотреть логи```bash

```python bot.py

```

Подробнее: [VDS_SETUP_GUIDE.md](VDS_SETUP_GUIDE.md)

## 📁 Структура проекта

## ⚙️ Конфигурация

```

Создайте файл `.env` на основе `.env.example`:zenithmedia_bot/

├── bot.py                      # Главный файл запуска

```env├── config.py                   # Конфигурация

BOT_TOKEN=your_bot_token_from_botfather├── database.py                 # Работа с базой данных

ADMIN_IDS=123456789,987654321├── keyboards.py                # Клавиатуры бота

ADMIN_CHAT_ID=-1001234567890├── utils.py                    # Вспомогательные функции

MIN_WITHDRAWAL=100├── crypto_pay.py               # Интеграция Crypto Bot API 🆕

REFERRAL_PERCENT=10├── tiktok_parser.py            # Парсинг TikTok видео

TIKTOK_PARSER_TEST_MODE=false├── youtube_parser.py           # Парсинг YouTube каналов

```├── youtube_video_parser.py     # Парсинг YouTube видео

├── migrate_add_tier.py         # Миграция БД (tier система)

### Получение токенов├── handlers/                   # Обработчики команд

│   ├── __init__.py

1. **BOT_TOKEN**: Получите у [@BotFather](https://t.me/BotFather)│   ├── profile.py              # Профиль пользователя

   - Отправьте `/newbot`│   ├── videos.py               # Просмотр видео

   - Следуйте инструкциям│   ├── tiktok.py               # TikTok видео 🆕

   - Скопируйте полученный токен│   ├── youtube.py              # YouTube каналы 🆕

│   ├── youtube_videos.py       # YouTube видео 🆕

2. **ADMIN_IDS**: Ваш Telegram ID│   ├── payments.py             # Способы выплат

   - Отправьте `/start` боту [@userinfobot](https://t.me/userinfobot)│   ├── payouts.py              # Система выплат Crypto Pay 🆕

   - Скопируйте ваш ID│   ├── referral.py             # Реферальная система

│   ├── help.py                 # Помощь

3. **ADMIN_CHAT_ID**: ID чата для уведомлений│   ├── admin.py                # Админ-панель

   - Создайте группу в Telegram│   └── admin_settings.py       # Управление ставками и уровнями 🆕

   - Добавьте бота в группу├── requirements.txt            # Зависимости

   - Добавьте [@userinfobot](https://t.me/userinfobot) в группу├── .env                        # Конфигурация (не в git)

   - Скопируйте ID группы (начинается с `-100`)├── .gitignore                  # Git ignore

├── README.md                   # Основная документация

4. **Crypto Bot**: Настройте в `config.py`├── TIER_SYSTEM_GUIDE.md        # Руководство по системе уровней 🆕

   - Зарегистрируйтесь в [@CryptoBot](https://t.me/CryptoBot)├── ADMIN_COMMANDS.md           # Справка админских команд 🆕

   - Создайте приложение и получите API токен├── CHANGELOG_TIERS.md          # История изменений 🆕

   - Укажите токен в `config.py` → `CRYPTO_PAY_TOKEN`└── CRYPTO_PAY_GUIDE.md         # Руководство по Crypto Pay

```

## 📖 Документация

## 💡 Использование

- [📘 Система уровней](TIER_SYSTEM_GUIDE.md) - Bronze и Gold тарифы

- [💰 Автоматические выплаты](AUTO_PAYMENTS_GUIDE.md) - Настройка авто-выплат### Для пользователей:

- [🤖 Crypto Bot API](CRYPTO_PAY_GUIDE.md) - Интеграция с Crypto Bot

- [📄 Создание счетов](INVOICE_GUIDE.md) - Пополнение баланса1. **Начало работы**: `/start`

- [👨‍💼 Админ команды](ADMIN_COMMANDS.md) - Список всех команд2. **Профиль**: Нажмите "👤 Профиль"

- [🖥️ Установка на VDS](VDS_SETUP_GUIDE.md) - Деплой на сервер3. **Добавить канал**: В профиле нажмите "➕ Добавить канал"

4. **Подать ролик**: Нажмите "🎬 Подать ролик"

## 🎯 Как это работает5. **Вывод средств**: Нажмите "💰 Вывод средств"

6. **Рефералы**: Нажмите "👥 Рефералы" для получения реферальной ссылки

### Для TikTok

### Для администраторов:

1. Пользователь отправляет ссылку на TikTok видео

2. Бот парсит количество просмотров**Основные:**

3. Рассчитывается заработок: `views / 1000 * 65₽`1. **Админ-панель**: `/admin`

4. Деньги зачисляются на баланс в боте2. **Статистика**: Просмотр общей статистики бота

5. Пользователь может вывести через Crypto Bot3. **Модерация**: Одобрение/отклонение видео через кнопки

4. **Выплаты**: Одобрение выплат → автоматическая отправка USDT

### Для YouTube

**Управление YouTube ставками:** 🆕

1. Пользователь привязывает свой YouTube канал- `/set_youtube_rate <user_id> <rate>` - установить индивидуальную ставку

2. Отправляет ссылку на новое видео (макс. 1 видео / 24ч)- `/get_rate <user_id>` - посмотреть текущую ставку

3. **Bronze**: Видео отправляется на проверку админу (ответ в течение 24ч)- При первом видео ютубера - кнопка "💰 Установить ставку"

4. **Gold**: Видео автоматически одобряется и оплачивается

5. Админ устанавливает индивидуальную фиксированную ставку за видео**Управление уровнями пользователей:** 🆕

6. Выплата автоматически отправляется на Crypto Bot кошелек- `/set_tier <user_id> <bronze/gold>` - установить уровень

- `/get_tier <user_id>` - посмотреть уровень

### Система уровней- Bronze: вывод через 24ч | Gold: моментальный вывод



#### 🥉 Bronze (по умолчанию)📖 **Подробнее:** см. `ADMIN_COMMANDS.md` и `TIER_SYSTEM_GUIDE.md`

- Ручная проверка видео админом

- Ответ в течение 24 часов## ⚙️ Конфигурация

- Вывод средств через запрос

### Параметры в `.env`:

#### 🥇 Gold (для проверенных)

- Автоматическое одобрение видео- `BOT_TOKEN` - токен Telegram бота (получить у @BotFather)

- Моментальная выплата- `ADMIN_IDS` - ID администраторов через запятую

- Без проверки админа- `MIN_WITHDRAWAL` - минимальная сумма для вывода (в рублях)

- Требуется установленная ставка- `REFERRAL_PERCENT` - процент от заработка реферала



## 🛠️ Технологии## 🗄️ База данных



- **aiogram 3.4.1** - Async Telegram Bot frameworkБот использует SQLite для хранения данных:

- **aiosqlite** - Async SQLite

- **yt-dlp** - YouTube/TikTok парсинг- **users** - пользователи (добавлено поле `tier` 🆕)

- **aiocryptopay** - Crypto Bot API клиент- **tiktok_accounts** - TikTok аккаунты с кодами верификации 🆕

- **SQLite** - База данных- **youtube_channels** - YouTube каналы с индивидуальными ставками 🆕

- **systemd** - Автозапуск на Linux- **videos** - поданные видео (TikTok + YouTube)

- **crypto_payouts** - запросы на выплаты через Crypto Pay 🆕

## 📁 Структура проекта- **withdrawal_requests** - старая система заявок (устаревшая)

- **payment_methods** - способы выплат

```- **referrals** - реферальные связи

zenithmedia_bot/

├── bot.py                      # Главный файл бота### Миграции:

├── config.py                   # Конфигурация```bash

├── database.py                 # Работа с базой данных# Добавление поля tier в users

├── crypto_pay.py               # Интеграция Crypto Botpython migrate_add_tier.py

├── keyboards.py                # Клавиатуры Telegram```

├── utils.py                    # Утилиты

├── tiktok_parser.py           # Парсер TikTok## 🔒 Безопасность

├── youtube_parser.py          # Парсер YouTube каналов

├── youtube_video_parser.py    # Парсер YouTube видео- Не храните `.env` файл в публичных репозиториях

├── handlers/                  # Обработчики команд- Регулярно делайте резервные копии базы данных

│   ├── admin.py              # Админ команды- Используйте сильные токены и ключи

│   ├── admin_settings.py     # Настройки ставок и уровней- Ограничьте доступ к админ-панели

│   ├── payments.py           # Платежи и выплаты

│   ├── profile.py            # Профиль пользователя## 📞 Поддержка

│   ├── referral.py           # Реферальная система

│   ├── tiktok.py             # Обработка TikTokЕсли у вас возникли вопросы или проблемы:

│   ├── youtube.py            # Обработка YouTube каналов- Создайте Issue в репозитории

│   └── youtube_videos.py     # Обработка YouTube видео- Свяжитесь с разработчиком

├── setup_vds.sh              # Автоустановка для VDS

├── bot_control.sh            # Управление ботом (создается при установке)## 📝 Лицензия

├── requirements.txt          # Python зависимости

├── .env                      # Конфигурация (не в git)MIT License

├── .env.example              # Пример конфигурации

└── .gitignore               # Git ignore файл## 🙏 Благодарности

```

- [aiogram](https://github.com/aiogram/aiogram) - асинхронная библиотека для Telegram Bot API

## 💡 Примеры использования- [aiosqlite](https://github.com/omnilib/aiosqlite) - асинхронная работа с SQLite



### Для пользователей---



```## 🎯 Что нового в версии 2.0

/start          - Начать работу с ботом

/profile        - Посмотреть профиль и баланс### ✅ Реализовано:

/help           - Помощь и инструкции- 🎵 Полная поддержка TikTok (парсинг, верификация, монетизация)

- 📺 Полная поддержка YouTube (каналы, видео, парсинг)

[📱 TikTok]     - Загрузить TikTok видео- 💰 Автоматические выплаты в USDT через Crypto Bot API

[🎥 YouTube]    - Управление YouTube каналом- 🥉🥇 Система уровней (Bronze/Gold) с разной скоростью выплат

[💰 Выплаты]    - Запросить выплату- 📊 Индивидуальные ставки для YouTube каналов

[👥 Рефералы]   - Реферальная программа- ⚡️ Быстрый парсинг через requests + fallback на yt-dlp

```- 🔐 Уникальные коды верификации для каждого пользователя

- 📤 Централизованные уведомления в админ-чат

### Для админов

### 📚 Документация:

```- `README.md` - основная документация (этот файл)

/admin                              - Открыть админ-панель- `TIER_SYSTEM_GUIDE.md` - полное руководство по системе уровней

/set_youtube_rate @user amount      - Установить ставку- `ADMIN_COMMANDS.md` - краткая справка админских команд

/set_tier @user gold                - Повысить до Gold- `CRYPTO_PAY_GUIDE.md` - руководство по Crypto Pay API

/create_invoice amount description  - Создать счет- `CHANGELOG_TIERS.md` - история изменений

```

### 🔧 Технологии:

## 🔧 Управление ботом (VDS)- aiogram 3.4.1 - фреймворк Telegram бота

- yt-dlp - парсинг видео

```bash- requests - быстрый парсинг

# Запуск/остановка- aiocryptopay - интеграция Crypto Bot

./bot_control.sh start- aiosqlite - асинхронная работа с БД

./bot_control.sh stop

./bot_control.sh restart---



# Мониторинг**⚠️ Production Checklist:**

./bot_control.sh status- ✅ Парсинг реальных просмотров (TikTok + YouTube)

./bot_control.sh logs- ✅ Интеграция с платежной системой (Crypto Pay)

- ⚠️ Система безопасности (требует доработки)

# Автозапуск- ⚠️ Продвинутый мониторинг и логирование

./bot_control.sh enable- ⚠️ Обработка edge cases

./bot_control.sh disable- ⚠️ Rate limiting для защиты от спама

```

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверьте логи
python bot.py

# Проверьте .env файл
cat .env

# Переустановите зависимости
pip install --force-reinstall -r requirements.txt
```

### Ошибки базы данных

```bash
# Очистить базу
python clear_database.py

# Или удалить полностью
rm bot_database.db
```

### Проблемы с Crypto Bot

1. Проверьте баланс: `/check_balance` в боте
2. Проверьте токен в `config.py`
3. Убедитесь что переводы включены в настройках Crypto Bot

## 📊 Статистика и мониторинг

Все операции логируются в:
- `journalctl -u zenithmedia-bot` (на VDS)
- Консоль (при ручном запуске)
- Админ-чат в Telegram

## 🔒 Безопасность

- ✅ Все секретные данные в `.env` (не коммитится в git)
- ✅ Проверка прав доступа для админ команд
- ✅ Безопасные выплаты через Crypto Bot API
- ✅ SQLite для надежного хранения данных

## 📝 Changelog

### Версия 2.0 (октябрь 2025)
- ✨ Добавлена система уровней (Bronze/Gold)
- ✨ Автоматические выплаты для Gold
- ✨ Ограничение 1 видео / 24 часа
- ✨ Улучшен парсинг даты YouTube видео
- ✨ Консолидированные админ уведомления
- 🔧 Исправлены ошибки Crypto Bot API
- 🔧 Исправлена ошибка базы данных (submitted_at → created_at)

### Версия 1.0
- 🎉 Первый релиз
- ✅ TikTok интеграция
- ✅ YouTube интеграция
- ✅ Crypto Bot выплаты
- ✅ Реферальная система

## 🤝 Контрибьюция

Pull requests приветствуются! Для больших изменений, пожалуйста, сначала откройте issue.

## 📄 Лицензия

[MIT](LICENSE)

## 👨‍💻 Автор

ZenithMedia Bot - Telegram бот для монетизации контента

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Отличный фреймворк для Telegram ботов
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Мощный инструмент для парсинга
- [Crypto Bot](https://t.me/CryptoBot) - API для криптовалютных платежей

---

⭐ **Понравился проект? Поставьте звезду!** ⭐
