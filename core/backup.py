import asyncio
import os
import subprocess
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Автоматический бэкап базы данных на GitHub каждые 24 часа"""
    
    def __init__(self, db_path: str = "bot_database.db", backup_interval: int = 86400):
        """
        Args:
            db_path: Путь к файлу базы данных
            backup_interval: Интервал бэкапа в секундах (по умолчанию 24 часа)
        """
        self.db_path = db_path
        self.backup_interval = backup_interval
        self.backup_dir = "backups"
        
    def create_backup_directory(self):
        """Создает директорию для бэкапов если её нет"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"✓ Создана директория для бэкапов: {self.backup_dir}")
    
    def backup_database(self):
        """Создает бэкап базы данных и загружает на GitHub"""
        try:
            # Проверяем существование БД
            if not os.path.exists(self.db_path):
                logger.warning(f"⚠️ База данных не найдена: {self.db_path}")
                return False
            
            # Создаем директорию для бэкапов
            self.create_backup_directory()
            
            # Имя файла с датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Копируем базу данных
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✓ Создан локальный бэкап: {backup_path}")
            
            # Загружаем на GitHub
            self.upload_to_github(backup_path, timestamp)
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Ошибка при создании бэкапа: {e}")
            return False
    
    def upload_to_github(self, backup_path: str, timestamp: str):
        """Загружает бэкап на GitHub"""
        try:
            # Добавляем файл в git
            subprocess.run(["git", "add", backup_path], check=True, capture_output=True)
            
            # Создаем коммит
            commit_message = f"backup: Database backup {timestamp}"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True
            )
            
            # Пушим на GitHub
            result = subprocess.run(
                ["git", "push"],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"✓ Бэкап загружен на GitHub: {backup_path}")
            logger.info(f"📤 Commit: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Ошибка при загрузке на GitHub: {e}")
            if e.output:
                logger.error(f"Output: {e.output}")
    
    async def start_auto_backup(self):
        """Запускает автоматический бэкап каждые 24 часа"""
        logger.info(f"🔄 Автобэкап запущен (интервал: {self.backup_interval / 3600:.1f} часов)")
        
        while True:
            try:
                # Делаем первый бэкап сразу
                logger.info("📦 Начинаю создание бэкапа...")
                self.backup_database()
                
                # Ждем следующего цикла
                logger.info(f"⏰ Следующий бэкап через {self.backup_interval / 3600:.1f} часов")
                await asyncio.sleep(self.backup_interval)
                
            except Exception as e:
                logger.error(f"✗ Ошибка в цикле автобэкапа: {e}")
                # Ждем 1 час перед повтором при ошибке
                await asyncio.sleep(3600)


# Глобальный экземпляр для использования в bot.py
backup_manager = DatabaseBackup()
