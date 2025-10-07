from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from bs4 import BeautifulSoup
import random
import string
import re
import logging
import asyncio

from core.database import Database
from core.keyboards import cancel_keyboard, tiktok_verification_keyboard
from core import config

logger = logging.getLogger(__name__)

router = Router()
db = Database(config.DATABASE_PATH)


def create_progress_bar(percent: int) -> str:
    """Создает прогресс-бар визуально"""
    filled = int(percent / 10)
    empty = 10 - filled
    return f"{'🟩' * filled}{'⬜' * empty} {percent}%"


async def update_progress_message(message: Message, title: str, steps: list, current_step: int, total_steps: int):
    """Обновляет сообщение с прогресс-баром"""
    percent = int((current_step / total_steps) * 100)
    progress_bar = create_progress_bar(percent)
    
    text = f"🔍 <b>{title}</b>\n\n{progress_bar}\n\n"
    
    for i, step in enumerate(steps):
        if i < current_step:
            text += f"✅ {step}\n"
        elif i == current_step:
            text += f"⏳ {step}\n"
        else:
            text += f"⏸️ {step}\n"
    
    try:
        await message.edit_text(text, parse_mode="HTML")
    except:
        pass


class TikTokStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_confirmation = State()


def generate_verification_code(user_id: int) -> str:
    """Генерация уникального кода верификации"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TG{user_id}{random_part}"


def extract_tiktok_username(url: str) -> str:
    """Извлечь username из TikTok URL"""
    # https://www.tiktok.com/@username
    # https://tiktok.com/@username
    # @username
    
    if url.startswith('@'):
        return url[1:]
    
    match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', url)
    if match:
        return match.group(1)
    
    return None


async def get_tiktok_profile_bio(username: str) -> str:
    """
    Получить био профиля TikTok используя HTTP запрос (быстро) или Playwright (резерв)
    Автоматически парсит страницу
    """
    url = f"https://www.tiktok.com/@{username}"
    
    # Метод 1: Пробуем HTTP запрос (быстро)
    try:
        import aiohttp
        from bs4 import BeautifulSoup
        import json
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем данные в script тегах
                    for script in soup.find_all('script'):
                        script_text = script.string or ''
                        if 'user' in script_text and 'signature' in script_text:
                            try:
                                # Пытаемся найти JSON с данными пользователя
                                json_match = re.search(r'{[^<>]*"signature"[^<>]*}', script_text)
                                if json_match:
                                    data = json.loads(json_match.group(0))
                                    bio = data.get('signature', '')
                                    if bio:
                                        logger.info(f"Bio found via HTTP for @{username}: {bio[:50]}")
                                        return bio
                            except:
                                continue
                    
                    # Также пробуем найти в meta тегах
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        content = meta_desc.get('content', '')
                        # В description часто есть био после имени пользователя
                        if content and len(content) > 10:
                            logger.info(f"Bio found via meta for @{username}: {content[:50]}")
                            return content
        
    except Exception as e:
        logger.warning(f"HTTP method failed for profile: {e}")
    
    # Метод 2: Используем Playwright (медленнее, но надежнее)
    try:
        from playwright.async_api import async_playwright
        import asyncio
        
        async with async_playwright() as p:
            # Запускаем headless браузер
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security'
                ]
            )
            
            # Создаем контекст с настройками
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ru-RU',
                timezone_id='Europe/Moscow',
                extra_http_headers={
                    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }
            )
            
            page = await context.new_page()
            
            try:
                # Переходим на страницу профиля с увеличенным таймаутом и другой стратегией
                try:
                    await page.goto(url, timeout=60000, wait_until='domcontentloaded')
                except Exception as e:
                    logger.warning(f"domcontentloaded failed, trying load: {e}")
                    await page.goto(url, timeout=60000, wait_until='load')
                
                # Ждем загрузки контента
                await page.wait_for_timeout(2000)
                
                # Метод 1: Ищем через селекторы
                bio_selectors = [
                    'h2[data-e2e="user-bio"]',
                    'h2.tiktok-bio',
                    '[data-e2e="user-subtitle"]',
                    'div.tiktok-1i0ztfr-DivInfoContainer h2',
                    'h2.tiktok-j2a19r-H2ShareDesc',
                ]
                
                bio_text = ""
                for selector in bio_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            bio_text = await element.inner_text()
                            if bio_text:
                                break
                    except:
                        continue
                
                # Метод 2: Ищем в JSON-LD данных
                if not bio_text:
                    try:
                        json_ld = await page.query_selector('script[type="application/ld+json"]')
                        if json_ld:
                            import json
                            content = await json_ld.inner_text()
                            data = json.loads(content)
                            bio_text = data.get('description', '')
                    except:
                        pass
                
                # Метод 3: Парсим весь HTML
                if not bio_text:
                    try:
                        html_content = await page.content()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Ищем все h2 теги
                        h2_tags = soup.find_all('h2')
                        for h2 in h2_tags:
                            text = h2.get_text(strip=True)
                            if text and len(text) > 10 and len(text) < 500:
                                bio_text = text
                                break
                    except:
                        pass
                
                await browser.close()
                
                print(f"[TikTok Parser] @{username} bio: {bio_text[:100] if bio_text else 'NOT FOUND'}")
                return bio_text
                
            except Exception as e:
                await browser.close()
                print(f"Ошибка при парсинге страницы: {e}")
                return ""
                
    except Exception as e:
        print(f"Ошибка при получении профиля TikTok: {e}")
        return ""


@router.callback_query(F.data == "add_tiktok")
async def start_tiktok_verification(callback: CallbackQuery, state: FSMContext):
    """Начать процесс верификации TikTok аккаунта"""
    
    # Проверяем, нет ли уже привязанного TikTok
    existing_tiktok = await db.get_user_tiktok(callback.from_user.id)
    if existing_tiktok:
        verified_status = "✅ Подтвержден" if existing_tiktok['is_verified'] else "⏳ Ожидает проверки"
        await callback.message.edit_text(
            f"ℹ️ <b>У вас уже привязан TikTok аккаунт</b>\n\n"
            f"🎵 Username: <code>@{existing_tiktok['username']}</code>\n"
            f"📊 Статус: {verified_status}\n\n"
            f"⚠️ <b>Один пользователь = один TikTok аккаунт</b>\n\n"
            f"Если хотите привязать другой аккаунт, обратитесь к администратору.",
            parse_mode="HTML"
        )
        await callback.answer("У вас уже есть TikTok аккаунт", show_alert=True)
        return
    
    # Генерируем код верификации
    verification_code = generate_verification_code(callback.from_user.id)
    await state.update_data(verification_code=verification_code)
    
    await callback.message.edit_text(
        f"🎵 <b>Привязка TikTok аккаунта</b>\n\n"
        f"Отправьте ссылку на ваш TikTok профиль:\n\n"
        f"Например: <code>https://www.tiktok.com/@username</code>\n"
        f"или просто: <code>@username</code>\n\n"
        f"⚠️ <b>Важно:</b> Один TikTok можно привязать только к одному аккаунту!",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(TikTokStates.waiting_for_url)
    await callback.answer()


@router.message(TikTokStates.waiting_for_url)
async def receive_tiktok_url(message: Message, state: FSMContext):
    """Получить TikTok URL и начать проверку"""
    
    url = message.text.strip()
    
    # Извлекаем username
    username = extract_tiktok_username(url)
    
    if not username:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Отправьте ссылку в одном из форматов:\n"
            "• <code>https://www.tiktok.com/@username</code>\n"
            "• <code>@username</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Проверяем, не привязан ли этот TikTok к другому пользователю
    existing = await db.get_tiktok_by_username(username)
    if existing:
        await message.answer(
            f"❌ <b>Этот TikTok аккаунт уже привязан!</b>\n\n"
            f"🎵 TikTok: <code>@{username}</code>\n"
            f"👤 Привязан к: {existing['full_name']}\n"
            f"🆔 ID: <code>{existing['user_id']}</code>\n\n"
            f"⚠️ <b>Один TikTok = один пользователь навсегда</b>\n\n"
            f"Если это ваш аккаунт, обратитесь к администратору.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    data = await state.get_data()
    verification_code = data['verification_code']
    
    await state.update_data(username=username, url=url)
    
    # Сохраняем профиль как неверифицированный
    tiktok_url = f"https://www.tiktok.com/@{username}"
    
    await message.answer(
        f"✅ <b>TikTok профиль найден!</b>\n\n"
        f"👤 Username: <code>@{username}</code>\n"
        f"🔗 Профиль: {tiktok_url}\n\n"
        f"<b>Проверка кода верификации:</b>\n\n"
        f"⚠️ <b>Важно!</b> Этот TikTok будет закреплен за вами навсегда.\n\n"
        f"<b>Для подтверждения:</b>\n"
        f"1️⃣ Добавьте код <code>{verification_code}</code> в описание профиля TikTok\n"
        f"2️⃣ Нажмите кнопку <b>\"✅ Поменял описание\"</b> ниже\n\n"
        f"<b>ИЛИ</b>\n\n"
        f"Отправьте скриншот профиля с видимым кодом в описании",
        reply_markup=tiktok_verification_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(TikTokStates.waiting_for_confirmation)


@router.message(TikTokStates.waiting_for_confirmation, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    """Получить скриншот профиля"""
    
    data = await state.get_data()
    username = data['username']
    verification_code = data['verification_code']
    url = data['url']
    
    # В реальном боте администратор должен вручную проверить скриншот
    # Для автоматизации можно использовать OCR (Tesseract)
    
    await message.answer(
        f"📸 <b>Скриншот получен!</b>\n\n"
        f"⏳ Заявка отправлена на проверку администратору.\n"
        f"Вы получите уведомление, когда аккаунт будет подтвержден.\n\n"
        f"👤 TikTok: <code>@{username}</code>\n"
        f"🔑 Код: <code>{verification_code}</code>",
        parse_mode="HTML"
    )
    
    # Уведомляем администраторов в админ-чат
    if config.ADMIN_CHAT_ID:
        try:
            await message.bot.send_photo(
                config.ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=(
                    f"🔔 <b>Новая заявка на верификацию TikTok</b>\n\n"
                    f"👤 Пользователь: {message.from_user.full_name}\n"
                    f"🆔 ID: <code>{message.from_user.id}</code>\n"
                    f"📱 Username: @{message.from_user.username or 'нет'}\n\n"
                    f"🎵 TikTok: <code>@{username}</code>\n"
                    f"🔗 Профиль: {url}\n"
                    f"🔑 Код верификации: <code>{verification_code}</code>\n\n"
                    f"Проверьте, что код присутствует в био профиля на скриншоте.\n\n"
                    f"Для одобрения: /approve_tiktok_{message.from_user.id}\n"
                    f"Для отклонения: /reject_tiktok_{message.from_user.id}"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в админ-чат: {e}")
    else:
        # Если админ-чат не настроен, отправляем всем админам
        for admin_id in config.ADMIN_IDS:
            try:
                await message.bot.send_photo(
                    admin_id,
                    photo=message.photo[-1].file_id,
                    caption=(
                        f"🔔 <b>Новая заявка на верификацию TikTok</b>\n\n"
                        f"👤 Пользователь: {message.from_user.full_name}\n"
                        f"🆔 ID: <code>{message.from_user.id}</code>\n"
                        f"📱 Username: @{message.from_user.username or 'нет'}\n\n"
                        f"🎵 TikTok: <code>@{username}</code>\n"
                        f"🔗 Профиль: {url}\n"
                        f"🔑 Код верификации: <code>{verification_code}</code>\n\n"
                        f"Проверьте, что код присутствует в био профиля на скриншоте.\n\n"
                        f"Для одобрения: /approve_tiktok_{message.from_user.id}\n"
                        f"Для отклонения: /reject_tiktok_{message.from_user.id}"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки админу: {e}")
    
    await state.clear()


@router.callback_query(F.data == "tiktok_confirm_bio", TikTokStates.waiting_for_confirmation)
async def confirm_bio_button(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Поменял описание'"""
    await callback.answer()
    
    data = await state.get_data()
    username = data['username']
    verification_code = data['verification_code']
    url = data['url']
    
    # Показываем прогресс проверки
    steps = [
        "Ожидание обновления кеша (20 сек)",
        "Загрузка профиля",
        "Парсинг описания",
        "Проверка кода верификации"
    ]
    
    await callback.message.edit_text(
        "🔍 <b>Автоматическая проверка...</b>\n\n"
        "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%\n\n"
        "⏳ Ожидание обновления кеша (20 сек)\n"
        "⏸️ Загрузка профиля\n"
        "⏸️ Парсинг описания\n"
        "⏸️ Проверка кода верификации",
        parse_mode="HTML"
    )
    
    try:
        # Шаг 1: Ожидание кеша TikTok (20 секунд с анимацией)
        for i in range(20):
            percent = int(((i + 1) / 20) * 40)  # 0-40% на первый шаг
            progress_bar = create_progress_bar(percent)
            text = (
                f"🔍 <b>Автоматическая проверка...</b>\n\n"
                f"{progress_bar}\n\n"
                f"⏳ Ожидание обновления кеша ({20 - i} сек)\n"
                f"⏸️ Загрузка профиля\n"
                f"⏸️ Парсинг описания\n"
                f"⏸️ Проверка кода верификации"
            )
            try:
                await callback.message.edit_text(text, parse_mode="HTML")
            except:
                pass
            await asyncio.sleep(1)
        
        # Шаг 2: Загрузка профиля (анимация 2 секунды)
        for i in range(4):
            percent = 40 + int(((i + 1) / 4) * 20)  # 40-60%
            progress_bar = create_progress_bar(percent)
            text = (
                f"🔍 <b>Автоматическая проверка...</b>\n\n"
                f"{progress_bar}\n\n"
                f"✅ Ожидание обновления кеша (20 сек)\n"
                f"⏳ Загрузка профиля...\n"
                f"⏸️ Парсинг описания\n"
                f"⏸️ Проверка кода верификации"
            )
            try:
                await callback.message.edit_text(text, parse_mode="HTML")
            except:
                pass
            await asyncio.sleep(0.5)
        
        # Шаг 3: Парсинг описания (выполняем реальный парсинг)
        percent = 60
        progress_bar = create_progress_bar(percent)
        text = (
            f"🔍 <b>Автоматическая проверка...</b>\n\n"
            f"{progress_bar}\n\n"
            f"✅ Ожидание обновления кеша (20 сек)\n"
            f"✅ Загрузка профиля\n"
            f"⏳ Парсинг описания...\n"
            f"⏸️ Проверка кода верификации"
        )
        try:
            await callback.message.edit_text(text, parse_mode="HTML")
        except:
            pass
        
        bio = await get_tiktok_profile_bio(username)
        
        # Шаг 4: Проверка кода (анимация 2 секунды)
        for i in range(4):
            percent = 60 + int(((i + 1) / 4) * 40)  # 60-100%
            progress_bar = create_progress_bar(percent)
            text = (
                f"🔍 <b>Автоматическая проверка...</b>\n\n"
                f"{progress_bar}\n\n"
                f"✅ Ожидание обновления кеша (20 сек)\n"
                f"✅ Загрузка профиля\n"
                f"✅ Парсинг описания\n"
                f"⏳ Проверка кода верификации..."
            )
            try:
                await callback.message.edit_text(text, parse_mode="HTML")
            except:
                pass
            await asyncio.sleep(0.5)
        
        # Завершено
        if bio and verification_code in bio:
            # ✅ Код найден автоматически!
            tiktok_url = f"https://www.tiktok.com/@{username}"
            
            # Сохраняем в базу данных TikTok аккаунтов
            result = await db.add_tiktok_account(
                callback.from_user.id, 
                username,
                tiktok_url,
                verification_code
            )
            
            if result['success']:
                # Верифицируем аккаунт
                await db.verify_tiktok_account(callback.from_user.id)
                
                await callback.message.edit_text(
                    f"✅ <b>TikTok аккаунт успешно подтвержден!</b>\n\n"
                    f"🎵 <code>@{username}</code>\n"
                    f"🔑 Код найден автоматически!\n\n"
                    f"🔒 <b>Аккаунт закреплен за вами навсегда</b>\n\n"
                    f"Теперь вы можете:\n"
                    f"• Удалить код из био профиля\n"
                    f"• Подавать ролики с этого аккаунта\n\n"
                    f"📋 Найденное био:\n<i>{bio[:150]}...</i>",
                    parse_mode="HTML"
                )
                
                # Уведомляем админов об успешной автоверификации
                from core.utils import send_to_admin_chat
                await send_to_admin_chat(
                    callback.bot,
                    f"✅ <b>Автоматическая верификация TikTok</b>\n\n"
                    f"👤 Пользователь: {callback.from_user.full_name} (@{callback.from_user.username})\n"
                    f"🆔 ID: <code>{callback.from_user.id}</code>\n"
                    f"🎵 TikTok: <code>@{username}</code>\n"
                    f"🔑 Код подтвержден автоматически"
                )
            elif result['error'] == 'tiktok_taken':
                await callback.message.edit_text(
                    f"❌ <b>Этот TikTok уже привязан!</b>\n\n"
                    f"🎵 TikTok: <code>@{username}</code>\n"
                    f"👤 Владелец: {result['owner_username']}\n"
                    f"🆔 ID: <code>{result['owner_id']}</code>\n\n"
                    f"Один TikTok = один пользователь навсегда.",
                    parse_mode="HTML"
                )
            elif result['error'] == 'user_has_tiktok':
                await callback.message.edit_text(
                    f"❌ <b>У вас уже есть TikTok аккаунт!</b>\n\n"
                    f"🎵 Привязан: <code>@{result['current_username']}</code>\n\n"
                    f"Один пользователь = один TikTok навсегда.",
                    parse_mode="HTML"
                )
            
            await state.clear()
            
        else:
            # ❌ Код не найден
            await callback.message.edit_text(
                f"❌ <b>Код не найден в описании профиля!</b>\n\n"
                f"📋 Найденное био:\n<i>{bio[:200] if len(bio) > 0 else 'Пусто'}</i>\n\n"
                f"<b>Что делать:</b>\n"
                f"1️⃣ Убедитесь, что код добавлен в био\n"
                f"2️⃣ Подождите 1-2 минуты (кеш TikTok)\n"
                f"3️⃣ Попробуйте еще раз: нажмите <b>✅ Поменял описание</b>\n\n"
                f"Или отправьте скриншот профиля для ручной проверки.",
                parse_mode="HTML",
                reply_markup=tiktok_verification_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error during TikTok verification: {e}")
        try:
            await callback.message.edit_text(
                f"❌ <b>Ошибка при проверке</b>\n\n"
                f"Техническая ошибка: {str(e)}\n\n"
                f"Заявка отправлена администратору для ручной проверки.",
                parse_mode="HTML"
            )
        except:
            await callback.message.answer(
                f"❌ <b>Ошибка при проверке</b>\n\n"
                f"Техническая ошибка: {str(e)}\n\n"
                f"Заявка отправлена администратору для ручной проверки.",
                parse_mode="HTML"
            )
        
        # Уведомляем админов об ошибке
        from core.utils import send_to_admin_chat
        await send_to_admin_chat(
            callback.bot,
            f"🔔 <b>Заявка TikTok (ошибка парсинга)</b>\n\n"
            f"👤 {callback.from_user.full_name} (@{callback.from_user.username})\n"
            f"🎵 <code>@{username}</code>\n"
            f"🔑 <code>{verification_code}</code>\n\n"
            f"/approve_tiktok_{callback.from_user.id}_{username}\n"
            f"/reject_tiktok_{callback.from_user.id}"
        )
        
        await state.clear()


@router.message(TikTokStates.waiting_for_confirmation, F.text)
async def confirm_manually(message: Message, state: FSMContext):
    """Ручное подтверждение пользователя (если написал текст вместо кнопки)"""
    
    await message.answer(
        "Пожалуйста, используйте кнопку <b>\"✅ Поменял описание\"</b> выше\n\n"
        "Или отправьте скриншот профиля с видимым кодом в описании.",
        reply_markup=tiktok_verification_keyboard(),
        parse_mode="HTML"
    )


# Команды для администратора
@router.message(F.text.startswith("/approve_tiktok_"))
async def admin_approve_tiktok(message: Message):
    """Администратор одобряет TikTok аккаунт"""
    if message.from_user.id not in config.ADMIN_IDS:
        return
    
    try:
        parts = message.text.split("_")
        user_id = int(parts[2])
        username = parts[3] if len(parts) > 3 else "unknown"
        
        # Проверяем, нет ли уже аккаунта
        user_tiktok = await db.get_user_tiktok(user_id)
        if user_tiktok:
            # Просто верифицируем существующий
            await db.verify_tiktok_account(user_id)
            await message.answer(
                f"✅ TikTok аккаунт @{user_tiktok['username']} верифицирован для пользователя {user_id}",
                parse_mode="HTML"
            )
        else:
            # Добавляем новый аккаунт (для ручной проверки без кода)
            tiktok_url = f"https://www.tiktok.com/@{username}"
            verification_code = generate_verification_code(user_id)
            
            result = await db.add_tiktok_account(user_id, username, tiktok_url, verification_code)
            
            if result['success']:
                # Сразу верифицируем
                await db.verify_tiktok_account(user_id)
                await message.answer(
                    f"✅ TikTok аккаунт @{username} одобрен и добавлен для пользователя {user_id}",
                    parse_mode="HTML"
                )
            elif result['error'] == 'tiktok_taken':
                await message.answer(
                    f"❌ TikTok @{username} уже привязан к пользователю {result['owner_id']} ({result['owner_username']})",
                    parse_mode="HTML"
                )
            else:
                await message.answer(f"❌ Ошибка: {result['error']}")
        
        # Уведомляем пользователя
        try:
            await message.bot.send_message(
                user_id,
                f"✅ <b>Ваш TikTok аккаунт подтвержден!</b>\n\n"
                f"🎵 <code>@{username}</code>\n\n"
                f"🔒 Аккаунт закреплен за вами навсегда\n\n"
                f"Теперь вы можете подавать ролики с этого аккаунта!",
                parse_mode="HTML"
            )
        except:
            pass
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(F.text.startswith("/reject_tiktok_"))
async def admin_reject_tiktok(message: Message):
    """Администратор отклоняет TikTok аккаунт"""
    if message.from_user.id not in config.ADMIN_IDS:
        return
    
    try:
        parts = message.text.split("_")
        user_id = int(parts[2])
        
        await message.answer(f"❌ Заявка для пользователя {user_id} отклонена")
        
        # Уведомляем пользователя
        try:
            await message.bot.send_message(
                user_id,
                f"❌ <b>Заявка на верификацию TikTok отклонена</b>\n\n"
                f"Причины:\n"
                f"• Код верификации не найден в профиле\n"
                f"• Неверный формат\n\n"
                f"Попробуйте еще раз или свяжитесь с поддержкой.",
                parse_mode="HTML"
            )
        except:
            pass
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

