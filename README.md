# 🎬 ZenithMedia Bot# 🎬 ZenithMedia Bot# ZenithMedia Bot



Telegram бот для монетизации контента с TikTok и YouTube. Автоматические выплаты через Crypto Bot API с системой уровней (Bronze/Gold).



[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)Telegram бот для монетизации контента с TikTok и YouTube. Автоматические выплаты через Crypto Bot API с системой уровней (Bronze/Gold).Telegram бот для монетизации видеоконтента TikTok и YouTube с автоматическими выплатами через Crypto Pay.

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[![Aiogram](https://img.shields.io/badge/Aiogram-3.4.1-blue)](https://docs.aiogram.dev/)



## 🌟 Возможности## 🌟 Возможности## 🚀 Возможности



### Для пользователей

- 📱 **TikTok интеграция** - Загрузка видео и автоматический подсчет просмотров (65₽/1K views)

- 🎥 **YouTube интеграция** - Привязка канала и фиксированная оплата за видео### Для пользователей### Основные функции

- 💰 **Автоматические выплаты** - Моментальные выплаты для Gold пользователей

- 🥇 **Система уровней** - Bronze (проверка 24ч) и Gold (моментально)- 📱 **TikTok интеграция** - Загрузка видео и автоматический подсчет просмотров- ✅ Регистрация и управление профилем

- 👥 **Реферальная программа** - 10% от заработка рефералов

- 💳 **Crypto Bot выплаты** - Безопасные выплаты в USDT через @CryptoBot- 🎥 **YouTube интеграция** - Привязка канала и фиксированная оплата за видео- 🎵 Привязка TikTok аккаунтов с автоматической верификацией



### Для администраторов- 💰 **Автоматические выплаты** - Моментальные выплаты для Gold пользователей- 📺 Привязка YouTube каналов с кодом верификации

- ⚙️ **Админ-панель** - Полный контроль через Telegram

- 📊 **Гибкие ставки** - Индивидуальная ставка для каждого YouTube канала- 🥇 **Система уровней** - Bronze (проверка 24ч) и Gold (моментально)- 🎬 Подача видео на монетизацию (TikTok и YouTube)

- 🎯 **Управление уровнями** - Повышение/понижение пользователей

- 💸 **Пополнение баланса** - Создание счетов через Crypto Bot- 👥 **Реферальная программа** - 10% от заработка рефералов- 💰 Автоматические выплаты в USDT через Crypto Bot

- 📈 **Статистика** - Отслеживание всех операций

- 💳 **Crypto Bot выплаты** - Безопасные выплаты в USDT через @CryptoBot- 📊 Парсинг статистики видео (просмотры, лайки, комментарии)

## 🚀 Быстрый старт

- 📜 История видео и выплат

### Требования

### Для администраторов

- Python 3.11+

- SQLite3- ⚙️ **Админ-панель** - Полный контроль через Telegram### Система уровней 🆕

- ffmpeg

- Telegram Bot Token- 📊 **Гибкие ставки** - Индивидуальная ставка для каждого YouTube канала- 🥉 **Bronze** - вывод через 24 часа (по умолчанию)

- Crypto Bot API Token

- 🎯 **Управление уровнями** - Повышение/понижение пользователей- 🥇 **Gold** - моментальный вывод средств

### Установка (Windows)

- 💸 **Пополнение баланса** - Создание счетов через Crypto Bot

```bash

# Клонировать репозиторий- 📈 **Статистика** - Отслеживание всех операций### Монетизация

git clone https://github.com/yourusername/zenithmedia-bot.git

cd zenithmedia-bot- **TikTok**: 65₽ за 1000 просмотров (фиксированная ставка)



# Создать виртуальное окружение## 🚀 Быстрый старт- **YouTube**: индивидуальная ставка для каждого канала

python -m venv venv

venv\Scripts\activate



# Установить зависимости### Требования### Реферальная программа

pip install -r requirements.txt

- 👥 10% от заработка рефералов

# Настроить конфигурацию

copy .env.example .env- Python 3.11+- � Уникальная реферальная ссылка для каждого пользователя

# Отредактируйте .env своими данными

- SQLite3

# Запустить бота

python bot.py- ffmpeg### Админ-панель 👑

```

- Telegram Bot Token- 📊 Статистика бота

### Установка (Linux/Ubuntu VDS)

- Crypto Bot API Token- ✅ Модерация видео

```bash

# Клонировать репозиторий- 💰 Одобрение выплат с автоматической отправкой USDT

git clone https://github.com/yourusername/zenithmedia-bot.git

cd zenithmedia-bot### Установка (Windows)- 🎯 Установка индивидуальных ставок для YouTube



# Запустить автоматическую установку- 🥉🥇 Управление уровнями пользователей

chmod +x scripts/setup_vds.sh

sudo ./scripts/setup_vds.sh```bash



# Управление ботом# Клонировать репозиторий## 📋 Требования

./bot_control.sh start    # Запустить

./bot_control.sh stop     # Остановитьgit clone https://github.com/yourusername/zenithmedia_bot.git

./bot_control.sh logs     # Смотреть логи

```cd zenithmedia_bot- Python 3.9+



📖 **Подробная инструкция**: [docs/VDS_SETUP_GUIDE.md](docs/VDS_SETUP_GUIDE.md)- SQLite3



## ⚙️ Конфигурация# Создать виртуальное окружение



Создайте файл `.env` на основе `.env.example`:python -m venv venv## 🛠️ Установка



```envvenv\Scripts\activate

BOT_TOKEN=your_bot_token_from_botfather

ADMIN_IDS=123456789,9876543211. Клонируйте репозиторий:

ADMIN_CHAT_ID=-1001234567890

MIN_WITHDRAWAL=100# Установить зависимости```bash

REFERRAL_PERCENT=10

TIKTOK_PARSER_TEST_MODE=falsepip install -r requirements.txtgit clone <repository-url>

```

cd zenithmedia_bot

### Получение токенов

# Настроить конфигурацию```

1. **BOT_TOKEN**: [@BotFather](https://t.me/BotFather) → `/newbot`

2. **ADMIN_IDS**: [@userinfobot](https://t.me/userinfobot) → `/start`copy .env.example .env

3. **ADMIN_CHAT_ID**: Создайте группу, добавьте бота и [@userinfobot](https://t.me/userinfobot)

4. **Crypto Bot**: [@CryptoBot](https://t.me/CryptoBot) → Создайте приложение# Отредактируйте .env своими данными2. Установите зависимости:



## 📖 Документация```bash



- [📘 Система уровней](docs/TIER_SYSTEM_GUIDE.md) - Bronze и Gold тарифы# Запустить ботаpip install -r requirements.txt

- [💰 Автоматические выплаты](docs/AUTO_PAYMENTS_GUIDE.md) - Настройка авто-выплат

- [🤖 Crypto Bot API](docs/CRYPTO_PAY_GUIDE.md) - Интеграция с Crypto Botpython bot.py```

- [📄 Создание счетов](docs/INVOICE_GUIDE.md) - Пополнение баланса

- [👨‍💼 Админ команды](docs/ADMIN_COMMANDS.md) - Список всех команд```

- [🖥️ Установка на VDS](docs/VDS_SETUP_GUIDE.md) - Деплой на сервер

- [📤 Загрузка на GitHub](docs/GITHUB_UPLOAD.md) - Инструкция по загрузке3. Создайте файл `.env` на основе `.env.example`:



## 🎯 Как это работает### Установка (Linux/Ubuntu VDS)```bash



### Для TikTokcp .env.example .env



1. Пользователь отправляет ссылку на TikTok видео```bash```

2. Бот парсит количество просмотров

3. Рассчитывается заработок: `views / 1000 * 65₽`# Клонировать репозиторий

4. Деньги зачисляются на баланс

5. Вывод через Crypto Botgit clone https://github.com/yourusername/zenithmedia_bot.git4. Отредактируйте `.env` и добавьте ваш токен бота:



### Для YouTubecd zenithmedia_bot```env



1. Привязка YouTube каналаBOT_TOKEN=your_bot_token_here

2. Отправка видео (макс. 1 видео / 24ч)

3. **Bronze**: Проверка админом → Выплата через запрос# Запустить автоматическую установкуADMIN_IDS=123456789,987654321

4. **Gold**: Автоодобрение → Моментальная выплата

5. Индивидуальная фиксированная ставкаchmod +x setup_vds.shMIN_WITHDRAWAL=100



## 🛠️ Технологииsudo ./setup_vds.shREFERRAL_PERCENT=10



- **aiogram 3.4.1** - Async Telegram Bot framework```

- **aiosqlite** - Async SQLite

- **yt-dlp** - YouTube/TikTok парсинг# Управление ботом

- **aiocryptopay** - Crypto Bot API клиент

- **SQLite** - База данных./bot_control.sh start    # Запустить## 🚀 Запуск

- **systemd** - Автозапуск на Linux

./bot_control.sh stop     # Остановить

## 📁 Структура проекта

./bot_control.sh logs     # Смотреть логи```bash

```

zenithmedia-bot/```python bot.py

├── bot.py                      # Главный файл бота

├── requirements.txt            # Python зависимости```

├── .env.example               # Пример конфигурации

├── .gitignore                 # Git ignoreПодробнее: [VDS_SETUP_GUIDE.md](VDS_SETUP_GUIDE.md)

│

├── core/                      # Основные модули## 📁 Структура проекта

│   ├── config.py             # Конфигурация

│   ├── database.py           # База данных## ⚙️ Конфигурация

│   ├── crypto_pay.py         # Crypto Bot API

│   ├── keyboards.py          # Клавиатуры```

│   └── utils.py              # Утилиты

│Создайте файл `.env` на основе `.env.example`:zenithmedia_bot/

├── handlers/                  # Обработчики команд

│   ├── admin.py              # Админ команды├── bot.py                      # Главный файл запуска

│   ├── admin_settings.py     # Настройки ставок/уровней

│   ├── payments.py           # Платежи```env├── config.py                   # Конфигурация

│   ├── payouts.py            # Выплаты

│   ├── profile.py            # ПрофильBOT_TOKEN=your_bot_token_from_botfather├── database.py                 # Работа с базой данных

│   ├── referral.py           # Реферальная система

│   ├── tiktok.py             # TikTokADMIN_IDS=123456789,987654321├── keyboards.py                # Клавиатуры бота

│   ├── youtube.py            # YouTube каналы

│   └── youtube_videos.py     # YouTube видеоADMIN_CHAT_ID=-1001234567890├── utils.py                    # Вспомогательные функции

│

├── parsers/                   # ПарсерыMIN_WITHDRAWAL=100├── crypto_pay.py               # Интеграция Crypto Bot API 🆕

│   ├── tiktok_parser.py      # Парсер TikTok

│   ├── youtube_parser.py     # Парсер YouTube каналовREFERRAL_PERCENT=10├── tiktok_parser.py            # Парсинг TikTok видео

│   └── youtube_video_parser.py # Парсер YouTube видео

│TIKTOK_PARSER_TEST_MODE=false├── youtube_parser.py           # Парсинг YouTube каналов

├── scripts/                   # Скрипты

│   └── setup_vds.sh          # Автоустановка VDS```├── youtube_video_parser.py     # Парсинг YouTube видео

│

└── docs/                      # Документация├── migrate_add_tier.py         # Миграция БД (tier система)

    ├── README.md

    ├── VDS_SETUP_GUIDE.md### Получение токенов├── handlers/                   # Обработчики команд

    ├── TIER_SYSTEM_GUIDE.md

    ├── AUTO_PAYMENTS_GUIDE.md│   ├── __init__.py

    ├── CRYPTO_PAY_GUIDE.md

    └── ...1. **BOT_TOKEN**: Получите у [@BotFather](https://t.me/BotFather)│   ├── profile.py              # Профиль пользователя

```

   - Отправьте `/newbot`│   ├── videos.py               # Просмотр видео

## 💡 Команды

   - Следуйте инструкциям│   ├── tiktok.py               # TikTok видео 🆕

### Для пользователей

   - Скопируйте полученный токен│   ├── youtube.py              # YouTube каналы 🆕

```

/start          - Начать работу с ботом│   ├── youtube_videos.py       # YouTube видео 🆕

/profile        - Профиль и баланс

/help           - Помощь2. **ADMIN_IDS**: Ваш Telegram ID│   ├── payments.py             # Способы выплат



[📱 TikTok]     - Загрузить TikTok видео   - Отправьте `/start` боту [@userinfobot](https://t.me/userinfobot)│   ├── payouts.py              # Система выплат Crypto Pay 🆕

[🎥 YouTube]    - YouTube канал

[💰 Выплаты]    - Запросить выплату   - Скопируйте ваш ID│   ├── referral.py             # Реферальная система

[👥 Рефералы]   - Реферальная программа

```│   ├── help.py                 # Помощь



### Для админов3. **ADMIN_CHAT_ID**: ID чата для уведомлений│   ├── admin.py                # Админ-панель



```   - Создайте группу в Telegram│   └── admin_settings.py       # Управление ставками и уровнями 🆕

/admin                              - Админ-панель

/set_youtube_rate @user amount      - Установить ставку   - Добавьте бота в группу├── requirements.txt            # Зависимости

/set_tier @user gold                - Повысить до Gold

/create_invoice amount description  - Создать счет   - Добавьте [@userinfobot](https://t.me/userinfobot) в группу├── .env                        # Конфигурация (не в git)

```

   - Скопируйте ID группы (начинается с `-100`)├── .gitignore                  # Git ignore

## 🔧 Управление (VDS)

├── README.md                   # Основная документация

```bash

./bot_control.sh start     # Запустить4. **Crypto Bot**: Настройте в `config.py`├── TIER_SYSTEM_GUIDE.md        # Руководство по системе уровней 🆕

./bot_control.sh stop      # Остановить

./bot_control.sh restart   # Перезапустить   - Зарегистрируйтесь в [@CryptoBot](https://t.me/CryptoBot)├── ADMIN_COMMANDS.md           # Справка админских команд 🆕

./bot_control.sh status    # Статус

./bot_control.sh logs      # Логи   - Создайте приложение и получите API токен├── CHANGELOG_TIERS.md          # История изменений 🆕

```

   - Укажите токен в `config.py` → `CRYPTO_PAY_TOKEN`└── CRYPTO_PAY_GUIDE.md         # Руководство по Crypto Pay

## 🐛 Решение проблем

```

Смотрите: [docs/VDS_SETUP_GUIDE.md](docs/VDS_SETUP_GUIDE.md#решение-проблем)

## 📖 Документация

## 🔒 Безопасность

## 💡 Использование

- ✅ Секретные данные в `.env` (не в git)

- ✅ Проверка прав доступа- [📘 Система уровней](TIER_SYSTEM_GUIDE.md) - Bronze и Gold тарифы

- ✅ Безопасные выплаты через Crypto Bot

- ✅ SQLite для хранения данных- [💰 Автоматические выплаты](AUTO_PAYMENTS_GUIDE.md) - Настройка авто-выплат### Для пользователей:



## 📝 Changelog- [🤖 Crypto Bot API](CRYPTO_PAY_GUIDE.md) - Интеграция с Crypto Bot



### Версия 2.0 (Октябрь 2025)- [📄 Создание счетов](INVOICE_GUIDE.md) - Пополнение баланса1. **Начало работы**: `/start`

- ✨ Система уровней (Bronze/Gold)

- ✨ Автоматические выплаты для Gold- [👨‍💼 Админ команды](ADMIN_COMMANDS.md) - Список всех команд2. **Профиль**: Нажмите "👤 Профиль"

- ✨ Ограничение 1 видео / 24 часа

- ✨ Улучшенный парсинг YouTube- [🖥️ Установка на VDS](VDS_SETUP_GUIDE.md) - Деплой на сервер3. **Добавить канал**: В профиле нажмите "➕ Добавить канал"

- ✨ Консолидированные админ уведомления

- 🔧 Исправлены ошибки Crypto Bot API4. **Подать ролик**: Нажмите "🎬 Подать ролик"

- 🔧 Исправлена ошибка БД

## 🎯 Как это работает5. **Вывод средств**: Нажмите "💰 Вывод средств"

### Версия 1.0

- 🎉 Первый релиз6. **Рефералы**: Нажмите "👥 Рефералы" для получения реферальной ссылки

- ✅ TikTok интеграция

- ✅ YouTube интеграция### Для TikTok

- ✅ Crypto Bot выплаты

- ✅ Реферальная система### Для администраторов:



## 🤝 Контрибьюция1. Пользователь отправляет ссылку на TikTok видео



Pull requests приветствуются! Для больших изменений откройте issue.2. Бот парсит количество просмотров**Основные:**



## 📄 Лицензия3. Рассчитывается заработок: `views / 1000 * 65₽`1. **Админ-панель**: `/admin`



[MIT](LICENSE)4. Деньги зачисляются на баланс в боте2. **Статистика**: Просмотр общей статистики бота



## 🙏 Благодарности5. Пользователь может вывести через Crypto Bot3. **Модерация**: Одобрение/отклонение видео через кнопки



- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework4. **Выплаты**: Одобрение выплат → автоматическая отправка USDT

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Парсинг видео

- [Crypto Bot](https://t.me/CryptoBot) - Криптовалютные платежи### Для YouTube



---**Управление YouTube ставками:** 🆕



<div align="center">1. Пользователь привязывает свой YouTube канал- `/set_youtube_rate <user_id> <rate>` - установить индивидуальную ставку



**⭐ Понравился проект? Поставьте звезду! ⭐**2. Отправляет ссылку на новое видео (макс. 1 видео / 24ч)- `/get_rate <user_id>` - посмотреть текущую ставку



Made with ❤️ for content creators3. **Bronze**: Видео отправляется на проверку админу (ответ в течение 24ч)- При первом видео ютубера - кнопка "💰 Установить ставку"



</div>4. **Gold**: Видео автоматически одобряется и оплачивается


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
