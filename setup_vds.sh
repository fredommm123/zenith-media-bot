#!/bin/bash

# ============================================
# ZenithMedia Bot - Автоматическая установка на Ubuntu VDS
# ============================================

set -e  # Остановка при ошибке

echo "🚀 Начинаю установку ZenithMedia Bot..."
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода успешных сообщений
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для вывода предупреждений
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Функция для вывода ошибок
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Проверка, что скрипт запущен на Ubuntu
if [ ! -f /etc/os-release ]; then
    error "Не удалось определить операционную систему"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    warning "Этот скрипт предназначен для Ubuntu, но попробуем продолжить..."
fi

# Получаем текущего пользователя и домашнюю директорию
CURRENT_USER=${SUDO_USER:-$USER}
if [ "$CURRENT_USER" = "root" ]; then
    error "Не запускайте скрипт напрямую от root. Используйте: sudo ./setup_vds.sh"
    exit 1
fi

HOME_DIR=$(eval echo ~$CURRENT_USER)
PROJECT_DIR="$HOME_DIR/zenithmedia_bot"
SERVICE_NAME="zenithmedia-bot"

echo "📁 Директория проекта: $PROJECT_DIR"
echo "👤 Пользователь: $CURRENT_USER"
echo ""

# 1. Обновление системы
echo "📦 Обновление системы..."
apt-get update -qq
success "Система обновлена"

# 2. Установка Python 3.11+
echo "🐍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "Установка Python 3..."
    apt-get install -y python3 python3-pip python3-venv
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    success "Python установлен (версия $PYTHON_VERSION)"
fi

# 3. Установка дополнительных зависимостей
echo "📚 Установка системных зависимостей..."
apt-get install -y git curl wget ffmpeg
success "Системные зависимости установлены"

# 4. Создание директории проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📂 Создание директории проекта..."
    mkdir -p "$PROJECT_DIR"
    chown $CURRENT_USER:$CURRENT_USER "$PROJECT_DIR"
    success "Директория создана"
else
    warning "Директория $PROJECT_DIR уже существует"
fi

# 5. Копирование файлов (если запускается из другой директории)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Копирование файлов проекта..."
    cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
    chown -R $CURRENT_USER:$CURRENT_USER "$PROJECT_DIR"
    success "Файлы скопированы"
fi

# 6. Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    sudo -u $CURRENT_USER python3 -m venv venv
    success "Виртуальное окружение создано"
else
    warning "Виртуальное окружение уже существует"
fi

# 7. Установка Python зависимостей
echo "📦 Установка Python зависимостей..."
sudo -u $CURRENT_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
success "Зависимости установлены"

# 8. Проверка конфигурации
if [ ! -f "$PROJECT_DIR/.env" ]; then
    warning ".env файл не найден!"
    echo ""
    echo "Создайте файл .env со следующими параметрами:"
    echo "----------------------------------------"
    cat << 'EOF'
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_admin_id_here
ADMIN_CHAT_ID=your_admin_chat_id_here
MIN_WITHDRAWAL=100
REFERRAL_PERCENT=10
TIKTOK_PARSER_TEST_MODE=false
EOF
    echo "----------------------------------------"
    echo ""
    read -p "Хотите создать .env файл сейчас? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Введите BOT_TOKEN: " bot_token
        read -p "Введите ADMIN_IDS (через запятую): " admin_ids
        read -p "Введите ADMIN_CHAT_ID: " admin_chat_id
        
        cat > "$PROJECT_DIR/.env" << EOF
BOT_TOKEN=$bot_token
ADMIN_IDS=$admin_ids
ADMIN_CHAT_ID=$admin_chat_id
MIN_WITHDRAWAL=100
REFERRAL_PERCENT=10
TIKTOK_PARSER_TEST_MODE=false
EOF
        chown $CURRENT_USER:$CURRENT_USER "$PROJECT_DIR/.env"
        success ".env файл создан"
    else
        warning "Не забудьте создать .env файл перед запуском!"
    fi
else
    success ".env файл найден"
fi

# 9. Создание systemd service
echo "⚙️  Создание systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=ZenithMedia Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

success "Systemd service создан"

# 10. Перезагрузка systemd и включение автозапуска
echo "🔄 Настройка автозапуска..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
success "Автозапуск настроен"

# 11. Создание скрипта управления
echo "🎮 Создание скрипта управления..."
cat > "$PROJECT_DIR/bot_control.sh" << 'EOF'
#!/bin/bash

SERVICE_NAME="zenithmedia-bot"

case "$1" in
    start)
        echo "🚀 Запуск бота..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "🛑 Остановка бота..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "📋 Логи бота (Ctrl+C для выхода):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    logs-full)
        echo "📋 Все логи бота:"
        sudo journalctl -u $SERVICE_NAME --no-pager
        ;;
    enable)
        echo "✓ Включение автозапуска..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "✗ Отключение автозапуска..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    *)
        echo "ZenithMedia Bot - Управление"
        echo ""
        echo "Использование: ./bot_control.sh [команда]"
        echo ""
        echo "Команды:"
        echo "  start       - Запустить бота"
        echo "  stop        - Остановить бота"
        echo "  restart     - Перезапустить бота"
        echo "  status      - Статус бота"
        echo "  logs        - Показать логи в реальном времени"
        echo "  logs-full   - Показать все логи"
        echo "  enable      - Включить автозапуск"
        echo "  disable     - Отключить автозапуск"
        exit 1
        ;;
esac
EOF

chmod +x "$PROJECT_DIR/bot_control.sh"
chown $CURRENT_USER:$CURRENT_USER "$PROJECT_DIR/bot_control.sh"
success "Скрипт управления создан"

# 12. Создание алиаса для удобства
if ! grep -q "alias bot=" "$HOME_DIR/.bashrc"; then
    echo "alias bot='$PROJECT_DIR/bot_control.sh'" >> "$HOME_DIR/.bashrc"
    success "Алиас 'bot' добавлен в .bashrc"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✓ Установка завершена успешно!${NC}"
echo "================================================"
echo ""
echo "📌 Команды управления:"
echo ""
echo "  ./bot_control.sh start      - Запустить бота"
echo "  ./bot_control.sh stop       - Остановить бота"
echo "  ./bot_control.sh restart    - Перезапустить бота"
echo "  ./bot_control.sh status     - Проверить статус"
echo "  ./bot_control.sh logs       - Смотреть логи"
echo ""
echo "Или используйте короткий алиас (после перезахода):"
echo "  bot start / bot stop / bot restart / bot status / bot logs"
echo ""
echo "🚀 Запустить бота сейчас?"
read -p "(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start $SERVICE_NAME
    sleep 2
    systemctl status $SERVICE_NAME --no-pager
    echo ""
    success "Бот запущен! Используйте './bot_control.sh logs' для просмотра логов"
else
    echo "Запустите бота командой: ./bot_control.sh start"
fi

echo ""
echo "Документация проекта: $PROJECT_DIR/README.md"
