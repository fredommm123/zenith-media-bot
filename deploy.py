#!/usr/bin/env python3
"""
Скрипт автоматического деплоя на VDS
Использование: python deploy.py
"""

import json
import subprocess
import sys
from datetime import datetime

try:
    import paramiko
except ImportError:
    print("❌ Необходимо установить paramiko: pip install paramiko")
    sys.exit(1)


def load_config():
    """Загрузить конфигурацию деплоя"""
    with open("deploy_config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def git_commit_and_push():
    """Коммит и push изменений в репозиторий"""
    print("📦 Коммит изменений...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(
            ["git", "commit", "-m", f"Auto deploy: {timestamp}"],
            check=False  # Игнорируем ошибку если нет изменений
        )
        
        print("📤 Push в репозиторий...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Git push завершен")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git операция завершилась с ошибкой: {e}")


def deploy_to_vds(config):
    """Деплой на VDS через SSH"""
    print(f"🔧 Подключение к VDS {config['vds_host']}...")
    
    # Создаем SSH клиент
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Подключаемся
        client.connect(
            hostname=config["vds_host"],
            username=config["vds_user"],
            password=config["vds_password"],
            timeout=30
        )
        print("✅ Подключение установлено")
        
        # Команды для выполнения
        commands = f"""
        cd {config['remote_path']} && \
        git pull origin main && \
        source venv/bin/activate && \
        pip install -r requirements.txt && \
        sudo systemctl restart {config['service_name']} && \
        sudo systemctl status {config['service_name']} --no-pager
        """
        
        print("🚀 Выполнение команд на сервере...")
        stdin, stdout, stderr = client.exec_command(commands)
        
        # Выводим результат
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')
        
        if output:
            print("📋 Вывод:")
            print(output)
        
        if errors and "warning" not in errors.lower():
            print("⚠️ Ошибки:")
            print(errors)
        
        print("✅ Команды выполнены успешно")
        
    except paramiko.AuthenticationException:
        print("❌ Ошибка аутентификации. Проверьте логин и пароль.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"❌ SSH ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    finally:
        client.close()


def main():
    """Главная функция"""
    print("🚀 Начинаем автоматический деплой на VDS...\n")
    
    # Загружаем конфигурацию
    try:
        config = load_config()
    except FileNotFoundError:
        print("❌ Файл deploy_config.json не найден!")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Ошибка чтения deploy_config.json!")
        sys.exit(1)
    
    # Git операции
    git_commit_and_push()
    
    print()
    
    # Деплой на сервер
    deploy_to_vds(config)
    
    print("\n✅ Деплой завершен успешно!")


if __name__ == "__main__":
    main()
