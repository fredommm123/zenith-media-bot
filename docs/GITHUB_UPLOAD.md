# 📤 Инструкция по загрузке проекта на GitHub

## Шаг 1: Создайте репозиторий на GitHub

1. Перейдите на https://github.com
2. Нажмите на кнопку "+" в правом верхнем углу
3. Выберите "New repository"
4. Заполните данные:
   - **Repository name**: `zenithmedia-bot` (или любое другое имя)
   - **Description**: `Telegram бот для монетизации контента с TikTok и YouTube`
   - **Public** или **Private** - на ваш выбор
   - ❌ **НЕ** создавайте README.md (он уже есть в проекте)
   - ❌ **НЕ** добавляйте .gitignore (он уже есть в проекте)
5. Нажмите "Create repository"

## Шаг 2: Подключите репозиторий

После создания репозитория GitHub покажет вам URL. Скопируйте его и выполните:

```powershell
# Замените YOUR_USERNAME и YOUR_REPO на ваши данные
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Или используйте SSH (если настроен):
# git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

**Пример:**
```powershell
git remote add origin https://github.com/dariusdev/zenithmedia-bot.git
```

## Шаг 3: Загрузите код на GitHub

```powershell
# Переименуйте ветку в main (если нужно)
git branch -M main

# Загрузите код
git push -u origin main
```

При первой загрузке GitHub может попросить авторизацию.

## Шаг 4: Проверьте результат

Перейдите на страницу вашего репозитория на GitHub и убедитесь, что:
- ✅ Все файлы загружены
- ✅ README.md отображается на главной странице
- ✅ Файл .env НЕ загружен (защищен .gitignore)
- ✅ База данных НЕ загружена (защищена .gitignore)

## 🔒 ВАЖНО: Безопасность

Файлы, которые НЕ должны попасть в репозиторий:
- ❌ `.env` - содержит токены и секреты
- ❌ `bot_database.db` - база данных с пользовательскими данными
- ❌ `__pycache__/` - временные файлы Python
- ❌ `venv/` - виртуальное окружение

Эти файлы защищены `.gitignore` и не будут загружены на GitHub.

## 📝 Обновление кода в будущем

После внесения изменений в код:

```powershell
# Добавить все изменения
git add .

# Создать коммит с описанием
git commit -m "Описание изменений"

# Загрузить на GitHub
git push
```

**Примеры коммитов:**
```powershell
git commit -m "Fix: Исправлена ошибка парсинга TikTok"
git commit -m "Feature: Добавлена новая команда /stats"
git commit -m "Update: Обновлена документация"
```

## 🌐 Клонирование на VDS

После загрузки на GitHub, на VDS можно установить так:

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Запустить автоустановку
chmod +x scripts/setup_vds.sh
sudo ./scripts/setup_vds.sh
```

## 🔄 Обновление на VDS

Когда вы обновили код на GitHub:

```bash
cd ~/zenithmedia_bot

# Загрузить новые изменения
git pull

# Перезапустить бота
./bot_control.sh restart
```

## 🎯 Быстрые команды

```powershell
# Проверить статус
git status

# Посмотреть изменения
git diff

# Посмотреть историю коммитов
git log --oneline

# Отменить последний коммит (если не push)
git reset --soft HEAD~1

# Посмотреть удаленные репозитории
git remote -v
```

## ✅ Готово!

Ваш проект теперь на GitHub и готов к использованию! 🎉

Следующие шаги:
1. Добавьте описание проекта на странице GitHub
2. Добавьте теги (topics) для лучшей видимости
3. Создайте releases для версий
4. Настройте GitHub Actions (если нужно)

---

**Успешной работы с GitHub! 🚀**
