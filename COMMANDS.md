# 📋 Полезные команды для управления ботом

## 🤖 Управление ботом (локально через bot_control.sh)

```bash
# Подключение к VDS
ssh root@185.176.94.108

# Переход в директорию бота
cd /zenithmedia_bot

# Запуск бота
./bot_control.sh start

# Остановка бота
./bot_control.sh stop

# Перезапуск бота
./bot_control.sh restart

# Статус бота
./bot_control.sh status

# Просмотр логов бота (Ctrl+C для выхода)
./bot_control.sh logs
```

## 🔧 Управление через systemd

```bash
# Запуск бота
systemctl start zenithmedia-bot

# Остановка бота
systemctl stop zenithmedia-bot

# Перезапуск бота
systemctl restart zenithmedia-bot

# Статус бота
systemctl status zenithmedia-bot

# Логи бота (последние 100 строк)
journalctl -u zenithmedia-bot -n 100

# Логи бота в реальном времени
journalctl -u zenithmedia-bot -f

# Включить автозапуск бота при перезагрузке VDS
systemctl enable zenithmedia-bot

# Отключить автозапуск
systemctl disable zenithmedia-bot
```

## 💾 Работа с базой данных

```bash
# Очистка базы данных (ВНИМАНИЕ: все данные будут удалены!)
cd /zenithmedia_bot
systemctl stop zenithmedia-bot
rm -f bot_database.db
systemctl start zenithmedia-bot

# Создание бекапа базы данных вручную
cp bot_database.db backups/backup_$(date +%Y%m%d_%H%M%S).db

# Просмотр размера базы данных
ls -lh bot_database.db

# Очистка всех бекапов
rm -rf backups/*.db
```

## 📁 Работа с файлами бота

```bash
# Просмотр структуры проекта
tree -L 2 /zenithmedia_bot

# Или через ls
ls -la /zenithmedia_bot

# Просмотр содержимого файла
cat /zenithmedia_bot/bot.py

# Редактирование файла (nano)
nano /zenithmedia_bot/core/config.py

# Поиск в файлах
grep -r "текст для поиска" /zenithmedia_bot

# Права доступа к файлам
chmod +x /zenithmedia_bot/bot_control.sh
```

## 🐍 Python и виртуальное окружение

```bash
# Активация виртуального окружения
source /zenithmedia_bot/venv/bin/activate

# Установка зависимостей
pip install -r /zenithmedia_bot/requirements.txt

# Обновление зависимости
pip install --upgrade aiogram

# Просмотр установленных пакетов
pip list

# Деактивация виртуального окружения
deactivate
```

## 📦 Git команды (для обновления бота)

```bash
cd /zenithmedia_bot

# Проверка статуса
git status

# Просмотр изменений
git diff

# Получение обновлений с GitHub
git pull origin main

# Отмена локальных изменений (ВНИМАНИЕ!)
git reset --hard HEAD

# Просмотр истории коммитов
git log --oneline -10

# Установка git (если не установлен)
apt install git -y
```

## 🔄 Обновление бота с локальной машины на VDS

```powershell
# Копирование файла на VDS (из Windows PowerShell)
scp "путь\к\файлу" root@185.176.94.108:/zenithmedia_bot/путь/к/файлу

# Пример: обновить handlers/tiktok.py
scp "C:\Users\dariu_2\OneDrive\Рабочий стол\zenithmedia_bot\handlers\tiktok.py" root@185.176.94.108:/zenithmedia_bot/handlers/tiktok.py

# После копирования - перезапустить бота
ssh root@185.176.94.108 "systemctl restart zenithmedia-bot"
```

## 📊 Мониторинг системы VDS

```bash
# Использование диска
df -h

# Использование памяти
free -h

# Процессы Python
ps aux | grep python

# Загрузка CPU
top -bn1 | head -20

# Использование памяти ботом
systemctl status zenithmedia-bot | grep Memory

# Перезагрузка VDS (ОСТОРОЖНО!)
reboot
```

## 🔐 Безопасность и настройки

```bash
# Просмотр переменных окружения бота
cat /zenithmedia_bot/.env

# Редактирование .env
nano /zenithmedia_bot/.env

# После изменения .env - перезапуск обязателен
systemctl restart zenithmedia-bot

# Просмотр логов безопасности
tail -f /var/log/auth.log

# Список активных SSH соединений
w
```

## 🚀 Быстрые команды (выполнение из Windows)

```powershell
# Перезапуск бота
ssh root@185.176.94.108 "systemctl restart zenithmedia-bot"

# Просмотр статуса
ssh root@185.176.94.108 "systemctl status zenithmedia-bot"

# Просмотр последних логов
ssh root@185.176.94.108 "journalctl -u zenithmedia-bot -n 50 --no-pager"

# Очистка базы данных
ssh root@185.176.94.108 "cd /zenithmedia_bot && systemctl stop zenithmedia-bot && rm -f bot_database.db && systemctl start zenithmedia-bot"

# Очистка бекапов
ssh root@185.176.94.108 "rm -rf /zenithmedia_bot/backups/*.db"

# Обновление и перезапуск
scp "файл" root@185.176.94.108:/zenithmedia_bot/файл ; ssh root@185.176.94.108 "systemctl restart zenithmedia-bot"
```

## 📝 Полезная информация

- **IP VDS**: 185.176.94.108
- **Домен**: plum-thulite.antiddos.pw
- **Путь к боту**: /zenithmedia_bot
- **Имя сервиса**: zenithmedia-bot.service
- **База данных**: bot_database.db
- **Логи**: journalctl -u zenithmedia-bot
- **Бот**: @zenithmedia_bot
- **GitHub**: https://github.com/fredommm123/zenith-media-bot

## ⚠️ Важные замечания

1. **Всегда делай бекап** перед изменениями базы данных
2. **Проверяй логи** после перезапуска бота
3. **Не забывай перезапускать** бота после изменения файлов
4. **Git не установлен** на VDS - нужно установить: `apt install git -y`
5. **Автобекап работает** каждые 24 часа (но git push не работает без git)
