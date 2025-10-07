# 🔐 Инструкция по авторизации GitHub

## Проблема
```
remote: Permission to fredommm123/zenith-media-bot.git denied
fatal: unable to access: The requested URL returned error: 403
```

## Решение: Personal Access Token

### Шаг 1: Создайте токен на GitHub

1. Перейдите: https://github.com/settings/tokens
2. Нажмите "Generate new token" → "Generate new token (classic)"
3. Настройте:
   - **Note**: `zenith-media-bot` (название)
   - **Expiration**: `No expiration` (или выберите срок)
   - **Scopes**: Отметьте:
     - ✅ `repo` (полный доступ к репозиториям)
4. Нажмите "Generate token"
5. **ВАЖНО**: Скопируйте токен (он больше не будет показан!)

### Шаг 2: Используйте токен для push

```powershell
# Удалите старый remote
git remote remove origin

# Добавьте с токеном (замените YOUR_TOKEN на ваш токен)
git remote add origin https://YOUR_TOKEN@github.com/fredommm123/zenith-media-bot.git

# Загрузите код
git push -u origin main
```

**Пример:**
```powershell
git remote remove origin
git remote add origin https://ghp_xxxxxxxxxxxxxxxxxxxx@github.com/fredommm123/zenith-media-bot.git
git push -u origin main
```

---

## Альтернатива: GitHub CLI (gh)

Если установлен GitHub CLI:

```powershell
# Авторизуйтесь
gh auth login

# Загрузите код
git push -u origin main
```

---

## Альтернатива: SSH ключ

### 1. Создайте SSH ключ
```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. Добавьте ключ на GitHub
- Скопируйте: `cat ~/.ssh/id_ed25519.pub`
- Вставьте: https://github.com/settings/ssh/new

### 3. Используйте SSH URL
```powershell
git remote remove origin
git remote add origin git@github.com:fredommm123/zenith-media-bot.git
git push -u origin main
```

---

## После успешной загрузки

Проверьте репозиторий: https://github.com/fredommm123/zenith-media-bot

✅ Готово! Ваш код на GitHub!
