# 🚀 Установка ZenithMedia Bot на Ubuntu VDS

Полное руководство по автоматической установке и настройке бота на VDS с Ubuntu.

## 📋 Требования

- Ubuntu 20.04 или новее
- Root доступ или sudo права
- Минимум 1GB RAM
- Минимум 10GB свободного места

## 🎯 Быстрая установка (один скрипт)

### Шаг 1: Подключение к VDS

```bash
ssh your_user@your_server_ip
```

### Шаг 2: Загрузка проекта

```bash
# Вариант 1: Если проект в Git репозитории
git clone https://github.com/yourusername/zenithmedia_bot.git
cd zenithmedia_bot

# Вариант 2: Загрузка через SCP с локальной машины
# На локальной машине выполните:
scp -r C:\Users\dariu_2\OneDrive\Рабочий стол\zenithmedia_bot your_user@your_server_ip:~/
```

### Шаг 3: Запуск автоустановки

```bash
cd zenithmedia_bot
chmod +x setup_vds.sh
sudo ./setup_vds.sh
```

Скрипт автоматически:
- ✅ Обновит систему
- ✅ Установит Python 3 и все зависимости
- ✅ Создаст виртуальное окружение
- ✅ Установит ffmpeg для обработки видео
- ✅ Создаст systemd service для автозапуска
- ✅ Настроит автоматический перезапуск при сбоях
- ✅ Создаст удобные команды управления

### Шаг 4: Настройка конфигурации

Во время установки скрипт предложит создать `.env` файл. Введите:

- **BOT_TOKEN**: Токен от @BotFather
- **ADMIN_IDS**: ID администраторов через запятую (например: `8438727098,7490082783`)
- **ADMIN_CHAT_ID**: ID чата для уведомлений (например: `-1003062896752`)

Или создайте вручную после установки:

```bash
nano ~/zenithmedia_bot/.env
```

```env
BOT_TOKEN=8464029591:AAEytslS4Pj9qUsoGV0LZg9P8LRggfpIIvo
ADMIN_IDS=8438727098,7490082783
ADMIN_CHAT_ID=-1003062896752
MIN_WITHDRAWAL=100
REFERRAL_PERCENT=10
TIKTOK_PARSER_TEST_MODE=false
```

## 🎮 Управление ботом

После установки доступны простые команды:

### Основные команды

```bash
# Из директории проекта
./bot_control.sh start      # Запустить бота
./bot_control.sh stop       # Остановить бота
./bot_control.sh restart    # Перезапустить бота
./bot_control.sh status     # Проверить статус
./bot_control.sh logs       # Смотреть логи в реальном времени
./bot_control.sh logs-full  # Все логи
```

### Короткий алиас (после перезахода в терминал)

```bash
bot start    # Запустить
bot stop     # Остановить
bot restart  # Перезапустить
bot status   # Статус
bot logs     # Логи
```

## 🔧 Продвинутое управление

### Systemd команды

```bash
# Запуск
sudo systemctl start zenithmedia-bot

# Остановка
sudo systemctl stop zenithmedia-bot

# Перезапуск
sudo systemctl restart zenithmedia-bot

# Статус
sudo systemctl status zenithmedia-bot

# Автозапуск включить
sudo systemctl enable zenithmedia-bot

# Автозапуск выключить
sudo systemctl disable zenithmedia-bot
```

### Просмотр логов

```bash
# Логи в реальном времени
sudo journalctl -u zenithmedia-bot -f

# Последние 100 строк
sudo journalctl -u zenithmedia-bot -n 100

# Логи за сегодня
sudo journalctl -u zenithmedia-bot --since today

# Логи с определенного времени
sudo journalctl -u zenithmedia-bot --since "2025-10-08 14:00:00"
```

## 🔄 Обновление бота

### После изменений в коде

```bash
cd ~/zenithmedia_bot

# Загрузить новые файлы (Git)
git pull

# Или загрузить через SCP с локальной машины
# scp -r новые_файлы your_user@your_server_ip:~/zenithmedia_bot/

# Перезапустить бота
./bot_control.sh restart
```

### Обновление зависимостей

```bash
cd ~/zenithmedia_bot
source venv/bin/activate
pip install --upgrade -r requirements.txt
deactivate

./bot_control.sh restart
```

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверить статус
./bot_control.sh status

# Посмотреть ошибки в логах
./bot_control.sh logs-full | tail -50

# Проверить .env файл
cat ~/zenithmedia_bot/.env

# Проверить права доступа
ls -la ~/zenithmedia_bot/
```

### База данных заблокирована

```bash
cd ~/zenithmedia_bot
./bot_control.sh stop
rm bot_database.db-journal  # Если существует
./bot_control.sh start
```

### Недостаточно прав

```bash
# Исправить права на файлы
sudo chown -R $USER:$USER ~/zenithmedia_bot
chmod +x ~/zenithmedia_bot/*.sh
```

### Проблемы с Python зависимостями

```bash
cd ~/zenithmedia_bot
source venv/bin/activate
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
deactivate

./bot_control.sh restart
```

## 📊 Мониторинг

### Проверка использования ресурсов

```bash
# Использование CPU и памяти
top -p $(pgrep -f "python.*bot.py")

# Или более подробно
htop -p $(pgrep -f "python.*bot.py")

# Использование диска
df -h
du -sh ~/zenithmedia_bot/
```

### Автоматические уведомления об ошибках

Systemd автоматически перезапускает бота при сбоях (настроено в service файле).

Для email уведомлений можно настроить OnFailure в systemd или использовать мониторинг типа Uptime Robot.

## 🔒 Безопасность

### Защита .env файла

```bash
chmod 600 ~/zenithmedia_bot/.env
```

### Настройка firewall

```bash
# Разрешить только SSH
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### Регулярные обновления системы

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot  # При необходимости
```

## 📁 Структура после установки

```
~/zenithmedia_bot/
├── venv/                    # Виртуальное окружение Python
├── bot.py                   # Основной файл бота
├── config.py               # Конфигурация
├── database.py             # База данных
├── .env                    # Секретные данные (НЕ коммитить!)
├── bot_database.db         # SQLite база
├── requirements.txt        # Зависимости Python
├── setup_vds.sh           # Скрипт установки
├── bot_control.sh         # Скрипт управления
└── handlers/              # Обработчики команд
```

## 🎯 Полезные команды

```bash
# Посмотреть, запущен ли бот
ps aux | grep bot.py

# Узнать сколько времени работает
systemctl show zenithmedia-bot | grep ActiveEnterTimestamp

# Перезагрузить конфигурацию systemd после изменений
sudo systemctl daemon-reload

# Посмотреть все systemd services
systemctl list-units --type=service

# Очистить старые логи journalctl (оставить только 3 дня)
sudo journalctl --vacuum-time=3d
```

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `./bot_control.sh logs`
2. Проверьте статус: `./bot_control.sh status`
3. Проверьте .env файл
4. Проверьте доступность Telegram API
5. Проверьте баланс Crypto Bot

## 📚 Дополнительные ресурсы

- [AUTO_PAYMENTS_GUIDE.md](AUTO_PAYMENTS_GUIDE.md) - Руководство по автоматическим выплатам
- [TIER_SYSTEM_GUIDE.md](TIER_SYSTEM_GUIDE.md) - Руководство по системе уровней
- [CRYPTO_PAY_GUIDE.md](CRYPTO_PAY_GUIDE.md) - Настройка Crypto Bot
- [INVOICE_GUIDE.md](INVOICE_GUIDE.md) - Создание счетов для пополнения

## ✅ Чеклист после установки

- [ ] Бот запущен и работает
- [ ] Автозапуск включен
- [ ] .env файл настроен правильно
- [ ] Логи показывают успешное подключение
- [ ] Команды в Telegram работают
- [ ] Crypto Bot настроен и подключен
- [ ] Admin панель доступна администраторам
- [ ] База данных создана
- [ ] Тестовая выплата прошла успешно

---

**Удачного использования! 🚀**
