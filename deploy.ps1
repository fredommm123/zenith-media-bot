# Автоматический деплой на VDS
# Использование: .\deploy.ps1

$ErrorActionPreference = "Stop"

# Загружаем конфигурацию
$config = Get-Content -Path "deploy_config.json" | ConvertFrom-Json

$VDS_HOST = $config.vds_host
$VDS_USER = $config.vds_user
$VDS_PASSWORD = $config.vds_password
$REMOTE_PATH = $config.remote_path
$SERVICE_NAME = $config.service_name

Write-Host "🚀 Начинаем деплой на VDS $VDS_HOST..." -ForegroundColor Green

# Коммитим все изменения
Write-Host "📦 Коммит изменений..." -ForegroundColor Cyan
git add .
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Auto deploy: $timestamp" -ErrorAction SilentlyContinue

# Пушим в репозиторий
Write-Host "📤 Push в репозиторий..." -ForegroundColor Cyan
git push origin main -ErrorAction SilentlyContinue

# Команды для выполнения на сервере
$commands = @"
cd $REMOTE_PATH
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart $SERVICE_NAME
sudo systemctl status $SERVICE_NAME --no-pager
"@

Write-Host "🔧 Подключение к VDS и выполнение команд..." -ForegroundColor Cyan

# Используем plink для подключения (часть PuTTY)
# Если plink не установлен, используем SSH
if (Get-Command plink -ErrorAction SilentlyContinue) {
    echo "y" | plink -ssh "$VDS_USER@$VDS_HOST" -pw "$VDS_PASSWORD" $commands
} else {
    # Используем sshpass если доступен
    Write-Host "⚠️ plink не найден. Используйте SSH вручную или установите PuTTY" -ForegroundColor Yellow
    Write-Host "Команды для выполнения на сервере:" -ForegroundColor Yellow
    Write-Host $commands -ForegroundColor White
    
    # Альтернатива: сохраняем команды в файл
    $commands | Out-File -FilePath "deploy_commands.sh" -Encoding UTF8
    Write-Host "✅ Команды сохранены в deploy_commands.sh" -ForegroundColor Green
}

Write-Host "✅ Деплой завершен!" -ForegroundColor Green
