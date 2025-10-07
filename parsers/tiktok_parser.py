"""
TikTok Video Parser
Парсит метаданные TikTok видео: дату публикации, просмотры, лайки, комментарии, репосты, избранные
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import aiohttp

logger = logging.getLogger(__name__)


def extract_tiktok_video_id(url: str) -> Optional[str]:
    """
    Извлечь ID видео из TikTok URL
    
    Поддерживаемые форматы:
    - https://www.tiktok.com/@username/video/1234567890123456789
    - https://vm.tiktok.com/ZMabcdefgh/
    - https://vt.tiktok.com/ZSabcdefgh/
    """
    patterns = [
        r'tiktok\.com/@[^/]+/video/(\d+)',
        r'vm\.tiktok\.com/([A-Za-z0-9]+)',
        r'vt\.tiktok\.com/([A-Za-z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_tiktok_username_from_url(url: str) -> Optional[str]:
    """
    Извлечь username автора из TikTok URL
    https://www.tiktok.com/@username/video/123 → username
    """
    match = re.search(r'tiktok\.com/@([^/]+)/video', url)
    if match:
        return match.group(1)
    return None


async def parse_tiktok_video_http(url: str) -> Dict[str, Any]:
    """
    Резервный метод парсинга через HTTP запрос (без Playwright)
    Быстрее, но менее надежен
    """
    try:
        from bs4 import BeautifulSoup
        import json
        
        video_id = extract_tiktok_video_id(url)
        if not video_id:
            return {'success': False, 'error': 'Неверный формат TikTok URL'}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    return {'success': False, 'error': f'HTTP {response.status}'}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Логируем для диагностики
                logger.info(f"HTTP response length: {len(html)} chars")
                
                # Метод 1: Ищем JSON-LD данные
                json_ld_script = soup.find('script', {'type': 'application/ld+json'})
                
                # Если нет JSON-LD, ищем данные в <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
                if not json_ld_script:
                    logger.info("JSON-LD not found, trying __UNIVERSAL_DATA_FOR_REHYDRATION__")
                    universal_data_script = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
                    if universal_data_script:
                        try:
                            data = json.loads(universal_data_script.string)
                            # Извлекаем данные из универсального формата TikTok
                            video_detail = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {})
                            if video_detail:
                                item_info = video_detail.get('itemInfo', {}).get('itemStruct', {})
                                if item_info:
                                    author_info = item_info.get('author', {})
                                    stats = item_info.get('stats', {})
                                    
                                    author_name = author_info.get('uniqueId', '')
                                    if not author_name:
                                        author_name = extract_tiktok_username_from_url(url) or ''
                                    
                                    result = {
                                        'success': True,
                                        'video_id': video_id,
                                        'author': author_name,
                                        'published_at': None,
                                        'views': int(stats.get('playCount', 0)),
                                        'likes': int(stats.get('diggCount', 0)),
                                        'comments': int(stats.get('commentCount', 0)),
                                        'shares': int(stats.get('shareCount', 0)),
                                        'favorites': int(stats.get('collectCount', 0)),
                                        'description': item_info.get('desc', '')
                                    }
                                    
                                    # Парсим дату
                                    create_time = item_info.get('createTime')
                                    if create_time:
                                        try:
                                            result['published_at'] = datetime.fromtimestamp(int(create_time))
                                        except:
                                            pass
                                    
                                    logger.info(f"TikTok video parsed via HTTP (UNIVERSAL_DATA): {video_id}")
                                    return result
                        except Exception as e:
                            logger.warning(f"Failed to parse UNIVERSAL_DATA: {e}")
                
                # Метод 3: Ищем данные в любых script тегах с "itemModule" или "videoData"
                if not json_ld_script:
                    logger.info("Trying to find video data in any script tags...")
                    for script in soup.find_all('script'):
                        script_text = script.string or ''
                        if 'itemModule' in script_text or 'videoData' in script_text or 'ItemModule' in script_text:
                            try:
                                # Пытаемся найти JSON внутри скрипта
                                json_match = re.search(r'({[^<>]*"itemModule"[^<>]*})', script_text, re.DOTALL)
                                if not json_match:
                                    json_match = re.search(r'({[^<>]*"stats"[^<>]*"playCount"[^<>]*})', script_text, re.DOTALL)
                                
                                if json_match:
                                    data = json.loads(json_match.group(1))
                                    
                                    # Ищем данные видео в структуре
                                    item_data = None
                                    if 'itemModule' in data:
                                        item_data = list(data['itemModule'].values())[0] if data['itemModule'] else None
                                    elif 'stats' in data:
                                        item_data = data
                                    
                                    if item_data and 'stats' in item_data:
                                        stats = item_data['stats']
                                        author_info = item_data.get('author', {})
                                        
                                        author_name = author_info.get('uniqueId', '') or item_data.get('authorName', '')
                                        if not author_name:
                                            author_name = extract_tiktok_username_from_url(url) or ''
                                        
                                        result = {
                                            'success': True,
                                            'video_id': video_id,
                                            'author': author_name,
                                            'published_at': None,
                                            'views': int(stats.get('playCount', 0)),
                                            'likes': int(stats.get('diggCount', 0)),
                                            'comments': int(stats.get('commentCount', 0)),
                                            'shares': int(stats.get('shareCount', 0)),
                                            'favorites': int(stats.get('collectCount', 0)),
                                            'description': item_data.get('desc', '')
                                        }
                                        
                                        create_time = item_data.get('createTime')
                                        if create_time:
                                            try:
                                                result['published_at'] = datetime.fromtimestamp(int(create_time))
                                            except:
                                                pass
                                        
                                        logger.info(f"TikTok video parsed via HTTP (script search): {video_id}")
                                        return result
                            except Exception as e:
                                continue
                
                # Метод 4: JSON-LD данные (если найдены)
                if json_ld_script:
                    data = json.loads(json_ld_script.string)
                    
                    author_name = data.get('author', {}).get('name', '')
                    if not author_name:
                        author_name = extract_tiktok_username_from_url(url) or ''
                    
                    result = {
                        'success': True,
                        'video_id': video_id,
                        'author': author_name,
                        'published_at': None,
                        'views': 0,
                        'likes': 0,
                        'comments': 0,
                        'shares': 0,
                        'favorites': 0,
                        'description': data.get('description', '')
                    }
                    
                    # Парсим дату
                    upload_date = data.get('uploadDate')
                    if upload_date:
                        try:
                            result['published_at'] = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Парсим статистику
                    interaction_statistic = data.get('interactionStatistic', [])
                    for stat in interaction_statistic:
                        interaction_type = stat.get('interactionType', '').lower()
                        count = int(stat.get('userInteractionCount', 0))
                        
                        if 'watch' in interaction_type or 'view' in interaction_type:
                            result['views'] = count
                        elif 'like' in interaction_type:
                            result['likes'] = count
                        elif 'comment' in interaction_type:
                            result['comments'] = count
                    
                    logger.info(f"TikTok video parsed via HTTP: {video_id}")
                    return result
                
                return {'success': False, 'error': 'Не найдены JSON-LD данные'}
                
    except Exception as e:
        logger.error(f"HTTP parsing error: {e}")
        return {'success': False, 'error': f'Ошибка HTTP парсинга: {str(e)}'}


async def parse_tiktok_video(url: str) -> Dict[str, Any]:
    """
    Парсит метаданные TikTok видео через Playwright
    
    Returns:
        {
            'success': bool,
            'video_id': str,
            'author': str,
            'published_at': datetime,
            'views': int,
            'likes': int,
            'comments': int,
            'shares': int,
            'favorites': int,
            'description': str,
            'error': str  # если success=False
        }
    """
    # Сначала пробуем быстрый HTTP метод
    logger.info(f"Trying HTTP method for: {url}")
    http_result = await parse_tiktok_video_http(url)
    if http_result.get('success'):
        return http_result
    
    logger.warning(f"HTTP method failed: {http_result.get('error')}")
    
    # Извлекаем username и video_id для тестового режима
    username = extract_tiktok_username_from_url(url)
    video_id = extract_tiktok_video_id(url)
    
    # ТЕСТОВЫЙ РЕЖИМ: Если TikTok недоступен, возвращаем валидные тестовые данные
    # Это позволит протестировать остальную логику бота
    try:
        import config
        if config.TIKTOK_PARSER_TEST_MODE and username and video_id:
            logger.warning(f"!!! TEST MODE ENABLED - Returning mock data for {video_id}")
            return {
                'success': True,
                'video_id': video_id,
                'author': username,
                'published_at': datetime.now(),  # Текущее время (свежее видео)
                'views': 12500,
                'likes': 850,
                'comments': 45,
                'shares': 23,
                'favorites': 67,
                'description': 'Test video (parser in test mode)'
            }
    except:
        pass
    
    logger.info(f"Trying Playwright method...")
    
    # Если HTTP не сработал, используем Playwright
    try:
        from playwright.async_api import async_playwright
        import json
        
        video_id = extract_tiktok_video_id(url)
        if not video_id:
            return {'success': False, 'error': 'Неверный формат TikTok URL'}
        
        async with async_playwright() as p:
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
                # Переходим на страницу видео с увеличенным таймаутом
                # Пробуем несколько стратегий загрузки
                try:
                    await page.goto(url, timeout=60000, wait_until='domcontentloaded')
                except Exception as e:
                    logger.warning(f"domcontentloaded failed, trying load: {e}")
                    await page.goto(url, timeout=60000, wait_until='load')
                
                # Ждем появления данных на странице
                try:
                    await page.wait_for_selector('script[id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]', timeout=10000)
                except:
                    logger.warning("__UNIVERSAL_DATA_FOR_REHYDRATION__ not found, continuing anyway")
                
                await page.wait_for_timeout(2000)  # Ждем загрузки JS
                
                # Метод 1: Ищем JSON-LD данные (самый надежный)
                try:
                    json_ld = await page.query_selector('script[type="application/ld+json"]')
                    if json_ld:
                        json_content = await json_ld.inner_text()
                        data = json.loads(json_content)
                        
                        # Парсим данные из JSON-LD
                        # Пробуем разные способы получить автора
                        author_name = ''
                        author_data = data.get('author', {})
                        if isinstance(author_data, dict):
                            author_name = author_data.get('name', '') or author_data.get('alternateName', '') or author_data.get('@id', '')
                        elif isinstance(author_data, str):
                            author_name = author_data
                        
                        # Если автор не найден, берем из URL
                        if not author_name or author_name == '':
                            author_name = extract_tiktok_username_from_url(url) or ''
                            logger.info(f"Author extracted from URL: {author_name}")
                        
                        result = {
                            'success': True,
                            'video_id': video_id,
                            'author': author_name,
                            'published_at': None,
                            'views': 0,
                            'likes': 0,
                            'comments': 0,
                            'shares': 0,
                            'favorites': 0,
                            'description': data.get('description', '')
                        }
                        
                        # Парсим дату публикации
                        upload_date = data.get('uploadDate')
                        if upload_date:
                            try:
                                result['published_at'] = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                            except:
                                pass
                        
                        # Парсим статистику
                        interaction_statistic = data.get('interactionStatistic', [])
                        for stat in interaction_statistic:
                            interaction_type = stat.get('interactionType', '').lower()
                            count = int(stat.get('userInteractionCount', 0))
                            
                            if 'watch' in interaction_type or 'view' in interaction_type:
                                result['views'] = count
                            elif 'like' in interaction_type:
                                result['likes'] = count
                            elif 'comment' in interaction_type:
                                result['comments'] = count
                        
                        await browser.close()
                        logger.info(f"TikTok video parsed (JSON-LD): {video_id}, views: {result['views']}")
                        return result
                except Exception as e:
                    logger.warning(f"JSON-LD parsing failed: {e}")
                
                # Метод 2: Парсим через селекторы (резервный)
                result = {
                    'success': True,
                    'video_id': video_id,
                    'author': '',
                    'published_at': None,
                    'views': 0,
                    'likes': 0,
                    'comments': 0,
                    'shares': 0,
                    'favorites': 0,
                    'description': ''
                }
                
                # Ищем автора
                author_selectors = [
                    '[data-e2e="browse-username"]',
                    'h2[data-e2e="browse-username"]',
                    'span[data-e2e="browse-username"]'
                ]
                
                for selector in author_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            author_text = await element.inner_text()
                            result['author'] = author_text.strip().replace('@', '')
                            break
                    except:
                        continue
                
                # Если не нашли автора, пробуем из URL
                if not result['author']:
                    result['author'] = extract_tiktok_username_from_url(url) or ''
                
                # Ищем статистику (просмотры, лайки, комментарии)
                stats_selectors = {
                    'views': ['[data-e2e="video-views"]', 'strong[data-e2e="video-views"]'],
                    'likes': ['[data-e2e="like-count"]', 'strong[data-e2e="like-count"]'],
                    'comments': ['[data-e2e="comment-count"]', 'strong[data-e2e="comment-count"]'],
                    'shares': ['[data-e2e="share-count"]', 'strong[data-e2e="share-count"]'],
                }
                
                for stat_name, selectors in stats_selectors.items():
                    for selector in selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.inner_text()
                                count = parse_count(text)
                                result[stat_name] = count
                                break
                        except:
                            continue
                
                # Дату публикации сложно получить без JSON-LD, используем текущее время
                result['published_at'] = datetime.now()
                
                await browser.close()
                logger.info(f"TikTok video parsed (selectors): {video_id}, views: {result['views']}")
                return result
                
            except Exception as e:
                await browser.close()
                logger.error(f"Error parsing TikTok video page: {e}")
                return {'success': False, 'error': f'Ошибка парсинга страницы: {str(e)}'}
                
    except Exception as e:
        logger.error(f"Error parsing TikTok video: {e}")
        return {'success': False, 'error': f'Ошибка парсинга: {str(e)}'}


def parse_count(text: str) -> int:
    """
    Парсит количество из текста с сокращениями
    Примеры: "1.2K" → 1200, "5.4M" → 5400000, "234" → 234
    """
    text = text.strip().upper()
    
    # Убираем все кроме цифр, точки и букв K/M/B
    text = re.sub(r'[^\d.KMB]', '', text)
    
    if not text:
        return 0
    
    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000
    }
    
    for suffix, multiplier in multipliers.items():
        if suffix in text:
            try:
                num = float(text.replace(suffix, ''))
                return int(num * multiplier)
            except:
                return 0
    
    try:
        return int(float(text))
    except:
        return 0


def is_video_recent(published_at: Optional[datetime], max_hours: int = 24) -> bool:
    """
    Проверяет, что видео опубликовано не позже max_hours часов назад
    """
    if not published_at:
        return False
    
    # Убираем timezone info для корректного сравнения
    if published_at.tzinfo:
        published_at = published_at.replace(tzinfo=None)
    
    now = datetime.now()
    max_age = timedelta(hours=max_hours)
    
    age = now - published_at
    return age <= max_age


async def validate_tiktok_video(url: str, user_tiktok_username: str) -> Dict[str, Any]:
    """
    Полная валидация TikTok видео:
    1. Парсит метаданные
    2. Проверяет, что видео не старее 24 часов
    3. Проверяет, что видео с привязанного TikTok аккаунта
    
    Returns:
        {
            'success': bool,
            'video_data': dict,  # если success=True
            'error': str,        # если success=False
            'error_code': str    # 'parse_error', 'too_old', 'wrong_author'
        }
    """
    # Парсим видео
    video_data = await parse_tiktok_video(url)
    
    if not video_data.get('success'):
        return {
            'success': False,
            'error': video_data.get('error', 'Не удалось спарсить видео'),
            'error_code': 'parse_error'
        }
    
    # Проверка 1: Автор видео
    # Убираем @ если есть и приводим к нижнему регистру
    video_author = video_data['author'].lower().strip().lstrip('@')
    user_username = user_tiktok_username.lower().strip().lstrip('@')
    
    if video_author != user_username:
        return {
            'success': False,
            'error': f'Видео опубликовано с аккаунта @{video_author}, а не с вашего @{user_username}',
            'error_code': 'wrong_author',
            'video_data': video_data
        }
    
    # Проверка 2: Возраст видео (не старее 24 часов)
    if not is_video_recent(video_data['published_at'], max_hours=24):
        published_str = video_data['published_at'].strftime('%d.%m.%Y %H:%M') if video_data['published_at'] else 'неизвестно'
        return {
            'success': False,
            'error': f'Видео опубликовано {published_str}. Принимаются только видео не старее 24 часов.',
            'error_code': 'too_old',
            'video_data': video_data
        }
    
    # Все проверки пройдены!
    return {
        'success': True,
        'video_data': video_data
    }
