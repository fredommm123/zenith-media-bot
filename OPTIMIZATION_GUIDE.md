# ⚡ Руководство по оптимизации и масштабированию ZenithMedia Bot

## 🎯 Текущие узкие места

### 1. База данных SQLite
**Проблемы:**
- Блокировки при записи (только один writer)
- Ограничение на размер БД (до 2TB)
- Нет репликации и масштабирования
- Медленные JOIN запросы на больших объемах

**Текущая нагрузка:** ~50-100 пользователей
**Максимальная нагрузка:** ~500-1000 пользователей

### 2. Синхронный парсинг видео
**Проблемы:**
- Блокировка бота при парсинге (до 30 сек на видео)
- Нет очереди задач
- Нет повторных попыток при ошибках

### 3. Отсутствие кэширования
**Проблемы:**
- Повторные запросы к БД для одних и тех же данных
- Нет кэша для результатов парсинга
- Нет кэша для курсов валют

## 📈 План оптимизации

### Этап 1: Быстрые улучшения (1-2 дня)

#### 1.1 Оптимизация запросов к БД
```python
# Добавить индексы для часто используемых полей
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created_at ON videos(created_at);
CREATE INDEX idx_users_balance ON users(balance);
CREATE INDEX idx_crypto_payouts_status ON crypto_payouts(status);
```

#### 1.2 Пул соединений для БД
```python
import asyncio
from contextlib import asynccontextmanager

class DatabasePool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
    
    async def init(self):
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.db_path)
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=30000")
            await self._pool.put(conn)
        self._initialized = True
    
    @asynccontextmanager
    async def acquire(self):
        conn = await self._pool.get()
        try:
            yield conn
        finally:
            await self._pool.put(conn)
```

#### 1.3 Простой кэш в памяти
```python
from functools import lru_cache
from typing import Optional
import time

class SimpleCache:
    def __init__(self, ttl: int = 300):  # 5 минут по умолчанию
        self.ttl = ttl
        self._cache = {}
    
    def get(self, key: str) -> Optional[any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: any):
        self._cache[key] = (value, time.time())
    
    def clear(self):
        self._cache.clear()

# Использование
cache = SimpleCache(ttl=600)  # 10 минут

async def get_user_stats(user_id: int):
    cache_key = f"user_stats_{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    stats = await db.get_user_stats(user_id)
    cache.set(cache_key, stats)
    return stats
```

### Этап 2: Средние улучшения (1 неделя)

#### 2.1 Миграция на PostgreSQL
```python
# Установка
pip install asyncpg

# Новый database.py
import asyncpg
from contextlib import asynccontextmanager

class PostgresDatabase:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None
    
    async def init(self):
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=10,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
    
    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection
    
    async def get_user(self, user_id: int):
        async with self.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
```

#### 2.2 Очередь задач с Celery
```python
# requirements.txt
celery[redis]==5.3.0
redis==5.0.0

# tasks.py
from celery import Celery
import asyncio

app = Celery('zenithmedia', broker='redis://localhost:6379')

@app.task(bind=True, max_retries=3)
def parse_video_task(self, url: str, platform: str):
    try:
        if platform == 'tiktok':
            result = asyncio.run(parse_tiktok_video(url))
        elif platform == 'youtube':
            result = asyncio.run(parse_youtube_video(url))
        return result
    except Exception as exc:
        # Повторная попытка через 60 секунд
        raise self.retry(exc=exc, countdown=60)

# Использование в боте
from tasks import parse_video_task

async def handle_video_submission(message: Message, url: str):
    # Отправляем задачу в очередь
    task = parse_video_task.delay(url, 'tiktok')
    
    # Сообщаем пользователю
    await message.answer("⏳ Видео отправлено на обработку...")
    
    # Сохраняем task_id для отслеживания
    await db.save_task(message.from_user.id, task.id)
```

#### 2.3 Redis для кэширования
```python
import aioredis
import json
from typing import Optional

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis_url = redis_url
        self.redis = None
    
    async def init(self):
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[dict]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: dict, ttl: int = 300):
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, ensure_ascii=False)
        )
    
    async def delete(self, key: str):
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

### Этап 3: Полное масштабирование (2-4 недели)

#### 3.1 Микросервисная архитектура
```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: ./bot
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/zenithmedia
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - parser-service
  
  parser-service:
    build: ./parser
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=zenithmedia
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  celery-worker:
    build: ./bot
    command: celery -A tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
```

#### 3.2 API Gateway
```python
# api_gateway.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

class VideoRequest(BaseModel):
    url: str
    user_id: int
    platform: str

@app.post("/api/v1/submit-video")
async def submit_video(request: VideoRequest):
    # Валидация
    if request.platform not in ['tiktok', 'youtube']:
        raise HTTPException(400, "Invalid platform")
    
    # Отправка в сервис парсинга
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://parser-service:8000/parse",
            json=request.dict()
        )
    
    return response.json()

@app.get("/api/v1/stats/{user_id}")
async def get_user_stats(user_id: int):
    # Проверка кэша
    cached = await redis.get(f"stats:{user_id}")
    if cached:
        return cached
    
    # Запрос к БД
    stats = await db.get_user_stats(user_id)
    
    # Сохранение в кэш
    await redis.set(f"stats:{user_id}", stats, ttl=300)
    
    return stats
```

## 📊 Мониторинг производительности

### Prometheus + Grafana
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Метрики
video_submissions = Counter(
    'video_submissions_total',
    'Total video submissions',
    ['platform', 'status']
)

processing_time = Histogram(
    'video_processing_seconds',
    'Video processing time',
    ['platform']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# Использование
@processing_time.time()
async def process_video(url: str, platform: str):
    start = time.time()
    try:
        result = await parse_video(url, platform)
        video_submissions.labels(platform=platform, status='success').inc()
        return result
    except Exception as e:
        video_submissions.labels(platform=platform, status='error').inc()
        raise
```

### Логирование с ELK Stack
```python
# logging_config.py
import logging
from pythonjsonlogger import jsonlogger

# Настройка JSON логирования
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Структурированное логирование
logger.info(
    "video_processed",
    extra={
        "user_id": user_id,
        "video_id": video_id,
        "platform": "tiktok",
        "views": 15000,
        "earnings": 975.0,
        "processing_time": 2.5
    }
)
```

## 🚀 Результаты оптимизации

### Ожидаемые показатели после оптимизации:

| Метрика | Сейчас | После Этапа 1 | После Этапа 2 | После Этапа 3 |
|---------|--------|---------------|---------------|---------------|
| Макс. пользователей | 500 | 1,000 | 5,000 | 50,000+ |
| Время отклика | 2-5 сек | 1-2 сек | 200-500 мс | 50-200 мс |
| Парсинг видео | 30 сек | 20 сек | 5-10 сек | 2-5 сек |
| Пропускная способность | 10 req/s | 50 req/s | 200 req/s | 1000+ req/s |
| Доступность | 95% | 98% | 99.5% | 99.9% |

## 💰 Оценка затрат на инфраструктуру

### Минимальная конфигурация (до 1000 пользователей)
- VPS: 2 vCPU, 4 GB RAM, 50 GB SSD - $20/месяц
- PostgreSQL (managed): $15/месяц
- Redis: $10/месяц
- **Итого: ~$45/месяц**

### Средняя конфигурация (до 5000 пользователей)
- VPS: 4 vCPU, 8 GB RAM, 100 GB SSD - $40/месяц
- PostgreSQL (managed): $30/месяц
- Redis: $20/месяц
- CDN: $10/месяц
- **Итого: ~$100/месяц**

### Производственная конфигурация (10000+ пользователей)
- Kubernetes кластер: 3 ноды - $150/месяц
- PostgreSQL (HA): $100/месяц
- Redis Cluster: $50/месяц
- Мониторинг: $30/месяц
- Резервное копирование: $20/месяц
- **Итого: ~$350/месяц**

## ✅ Чек-лист внедрения

- [ ] Создать бэкап текущей БД
- [ ] Добавить индексы в SQLite
- [ ] Реализовать простой кэш
- [ ] Настроить пул соединений
- [ ] Развернуть Redis
- [ ] Мигрировать на PostgreSQL
- [ ] Настроить Celery для фоновых задач
- [ ] Реализовать API Gateway
- [ ] Настроить мониторинг
- [ ] Провести нагрузочное тестирование
- [ ] Документировать изменения

---

*Документ подготовлен: 2025-10-09*
*Версия: 1.0*
