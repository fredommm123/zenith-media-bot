# Скрипт для загрузки изменений на VDS
# PowerShell скрипт

$VDS_IP = "185.176.94.108"
$VDS_USER = "root"
$VDS_PATH = "/zenithmedia_bot"
$LOCAL_PATH = $PSScriptRoot

Write-Host "🚀 Загрузка изменений на VDS..." -ForegroundColor Green
Write-Host "📍 VDS: $VDS_USER@$VDS_IP" -ForegroundColor Cyan
Write-Host ""

# Функция для копирования файла
function Copy-FileToVDS {
    param (
        [string]$LocalFile,
        [string]$RemoteFile
    )
    
    $fullLocalPath = Join-Path $LOCAL_PATH $LocalFile
    $fullRemotePath = "${VDS_USER}@${VDS_IP}:${VDS_PATH}/${RemoteFile}"
    
    if (Test-Path $fullLocalPath) {
        Write-Host "📤 $LocalFile..." -NoNewline
        scp $fullLocalPath $fullRemotePath 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
        } else {
            Write-Host " ❌" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  $LocalFile - файл не найден" -ForegroundColor Yellow
    }
}

Write-Host "📦 Загрузка измененных файлов..." -ForegroundColor Yellow
Write-Host ""

# Core модули
Write-Host "🔧 Core модули:" -ForegroundColor Cyan
Copy-FileToVDS "core\config.py" "core/config.py"
Copy-FileToVDS "core\database.py" "core/database.py"
Copy-FileToVDS "core\rate_limiter.py" "core/rate_limiter.py"
Copy-FileToVDS "core\validators.py" "core/validators.py"

Write-Host ""

# Handlers
Write-Host "🎮 Handlers:" -ForegroundColor Cyan
Copy-FileToVDS "handlers\payouts.py" "handlers/payouts.py"
Copy-FileToVDS "handlers\admin_settings.py" "handlers/admin_settings.py"
Copy-FileToVDS "handlers\admin.py" "handlers/admin.py"
Copy-FileToVDS "handlers\help.py" "handlers/help.py"

Write-Host ""

# Главный файл
Write-Host "🤖 Основные файлы:" -ForegroundColor Cyan
Copy-FileToVDS "bot.py" "bot.py"

Write-Host ""

# Скрипты
Write-Host "📜 Скрипты:" -ForegroundColor Cyan
Copy-FileToVDS "scripts\optimize_database.py" "scripts/optimize_database.py"

Write-Host ""

# Конфигурация
Write-Host "⚙️  Конфигурация:" -ForegroundColor Cyan
Copy-FileToVDS ".env.example" ".env.example"

Write-Host ""

# Документация
Write-Host "📖 Документация:" -ForegroundColor Cyan
Copy-FileToVDS "docs\TIER_SYSTEM_GUIDE.md" "docs/TIER_SYSTEM_GUIDE.md"
Copy-FileToVDS "TIER_SYSTEM_UPDATE.md" "TIER_SYSTEM_UPDATE.md"
Copy-FileToVDS "SECURITY_AND_OPTIMIZATION_APPLIED.md" "SECURITY_AND_OPTIMIZATION_APPLIED.md"

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

# Проверка и создание .env на VDS
Write-Host "🔐 Проверка .env файла на VDS..." -ForegroundColor Yellow

$checkEnv = ssh ${VDS_USER}@${VDS_IP} "[ -f ${VDS_PATH}/.env ] && echo 'exists' || echo 'missing'"

if ($checkEnv -like "*missing*") {
    Write-Host "⚠️  .env файл НЕ НАЙДЕН на VDS!" -ForegroundColor Red
    Write-Host ""
    Write-Host "❗ КРИТИЧНО: Создайте .env файл на VDS!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Выполните на VDS:" -ForegroundColor Yellow
    Write-Host "  1. ssh root@185.176.94.108" -ForegroundColor White
    Write-Host "  2. cd /zenithmedia_bot" -ForegroundColor White
    Write-Host "  3. cp .env.example .env" -ForegroundColor White
    Write-Host "  4. nano .env" -ForegroundColor White
    Write-Host "  5. Заполните все токены!" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "✅ .env файл найден на VDS" -ForegroundColor Green
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

# Перезапуск бота
Write-Host "🔄 Перезапуск бота на VDS..." -ForegroundColor Yellow
Write-Host ""

$restart = Read-Host "Перезапустить бота сейчас? (y/n)"

if ($restart -eq "y" -or $restart -eq "Y") {
    Write-Host "⏸️  Остановка бота..." -NoNewline
    ssh ${VDS_USER}@${VDS_IP} "systemctl stop zenithmedia-bot" 2>$null
    Start-Sleep -Seconds 2
    Write-Host " ✅" -ForegroundColor Green
    
    Write-Host "▶️  Запуск бота..." -NoNewline
    ssh ${VDS_USER}@${VDS_IP} "systemctl start zenithmedia-bot" 2>$null
    Start-Sleep -Seconds 3
    Write-Host " ✅" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "📊 Проверка статуса..." -ForegroundColor Cyan
    ssh ${VDS_USER}@${VDS_IP} "systemctl status zenithmedia-bot --no-pager -l" 2>$null | Select-Object -First 10
    
    Write-Host ""
    Write-Host "📋 Последние логи:" -ForegroundColor Cyan
    ssh ${VDS_USER}@${VDS_IP} "journalctl -u zenithmedia-bot -n 20 --no-pager" 2>$null
} else {
    Write-Host "ℹ️  Бот НЕ перезапущен" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Для перезапуска выполните:" -ForegroundColor Cyan
    Write-Host "  ssh root@185.176.94.108 'systemctl restart zenithmedia-bot'" -ForegroundColor White
}

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""
Write-Host "✅ Загрузка завершена!" -ForegroundColor Green
Write-Host ""
Write-Host "Важные напоминания:" -ForegroundColor Yellow
Write-Host "  1. Убедитесь что .env файл создан и заполнен!" -ForegroundColor White
Write-Host "  2. Получите НОВЫЙ токен Crypto Bot" -ForegroundColor White
Write-Host "  3. Запустите оптимизацию БД" -ForegroundColor White
Write-Host "  4. Проверьте логи" -ForegroundColor White
Write-Host ""
