import asyncio
import re
import logging
from typing import Optional, Dict, Any
import yt_dlp

logger = logging.getLogger(__name__)


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """Извлечь channel ID или handle из URL YouTube"""
    url = url.strip()
    
    # Если просто @handle
    if url.startswith('@'):
        return url
    
    # Парсим URL
    patterns = [
        r'youtube\.com/@([\w-]+)',
        r'youtube\.com/c/([\w-]+)',
        r'youtube\.com/channel/(UC[\w-]+)',
        r'youtube\.com/user/([\w-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def normalize_youtube_url(identifier: str) -> str:
    """Нормализовать URL YouTube канала"""
    if identifier.startswith('@'):
        return f"https://www.youtube.com/{identifier}"
    elif identifier.startswith('UC'):
        return f"https://www.youtube.com/channel/{identifier}"
    else:
        return f"https://www.youtube.com/@{identifier}"


async def parse_youtube_channel(url: str) -> Optional[Dict[str, Any]]:
    """
    Парсинг YouTube канала через yt-dlp
    Извлекает: channel_id, channel_name, description, subscriber_count
    """
    try:
        logger.info(f"Парсинг YouTube канала: {url}")
        
        # Настройки yt-dlp (без куков для быстрого парсинга)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # Быстрый режим
            'skip_download': True,
            'ignoreerrors': True,
            'socket_timeout': 15,  # Сокращенный таймаут
            'no_check_certificate': True,
            'prefer_insecure': True,
        }
        
        # Запускаем в отдельном потоке с таймаутом
        loop = asyncio.get_event_loop()
        
        try:
            channel_info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: _extract_channel_info(url, ydl_opts)
                ),
                timeout=30.0  # Сокращен до 30 секунд
            )
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при парсинге канала: {url} (>30 сек)")
            return None
        
        if not channel_info:
            logger.error(f"Не удалось получить информацию о канале: {url}")
            return None
        
        logger.info(f"✅ Канал распарсен: {channel_info['channel_name']} ({channel_info.get('subscriber_text', 'N/A')})")
        logger.info(f"   Channel ID: {channel_info.get('channel_id', 'N/A')}")
        logger.info(f"   Handle: {channel_info.get('channel_handle', 'N/A')}")
        logger.info(f"   Описание: {len(channel_info.get('description', ''))} символов")
        
        return channel_info
        
    except Exception as e:
        logger.error(f"Ошибка парсинга YouTube: {type(e).__name__} - {str(e)}")
        return None


def _extract_channel_info(url: str, ydl_opts: dict) -> Optional[Dict[str, Any]]:
    """Вспомогательная функция для извлечения информации (запускается в отдельном потоке)"""
    try:
        # Сначала пробуем быстрый метод через requests
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Извлекаем описание через regex
                desc_match = re.search(r'"description":"([^"]*)"', html)
                description = desc_match.group(1) if desc_match else ''
                
                # Извлекаем channel ID
                channel_id_match = re.search(r'"channelId":"(UC[\w-]+)"', html)
                channel_id = channel_id_match.group(1) if channel_id_match else None
                
                # Извлекаем имя канала
                name_match = re.search(r'"author":"([^"]+)"', html)
                channel_name = name_match.group(1) if name_match else 'Unknown'
                
                # Извлекаем handle
                handle_match = re.search(r'@([\w-]+)', url)
                channel_handle = '@' + handle_match.group(1) if handle_match else None
                
                if channel_id and description:
                    logger.info(f"✅ Быстрый парсинг успешен для {url}")
                    return {
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'channel_handle': channel_handle,
                        'description': description,
                        'subscriber_count': 0,
                        'subscriber_text': 'N/A'
                    }
        except Exception as e:
            logger.warning(f"Быстрый парсинг не удался: {e}")
        
        # Если быстрый метод не сработал, используем yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Извлекаем информацию о канале
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None
            
            # Получаем данные канала
            channel_id = info.get('channel_id') or info.get('uploader_id')
            channel_name = info.get('channel') or info.get('uploader')
            channel_url = info.get('channel_url') or info.get('uploader_url')
            description = info.get('description', '')
            
            # Извлекаем handle из URL
            channel_handle = None
            if channel_url:
                handle_match = re.search(r'@([\w-]+)', channel_url)
                if handle_match:
                    channel_handle = '@' + handle_match.group(1)
            
            # Количество подписчиков
            subscriber_count = info.get('channel_follower_count', 0)
            
            # Форматируем количество подписчиков
            if subscriber_count >= 1000000:
                subscriber_text = f"{subscriber_count / 1000000:.1f} млн"
            elif subscriber_count >= 1000:
                subscriber_text = f"{subscriber_count / 1000:.1f} тыс"
            else:
                subscriber_text = str(subscriber_count)
            
            subscriber_text += " подписчиков"
            
            return {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'channel_handle': channel_handle,
                'description': description,
                'subscriber_count': subscriber_count,
                'subscriber_text': subscriber_text
            }
            
    except Exception as e:
        logger.error(f"Ошибка в _extract_channel_info: {type(e).__name__} - {str(e)}")
        return None


def validate_youtube_url(url: str) -> bool:
    """Проверить валидность URL YouTube канала"""
    if not url or len(url) < 2:
        return False
    
    # Разрешаем @handle
    if url.startswith('@') and len(url) > 1:
        return True
    
    # Разрешаем UC...
    if url.startswith('UC') and len(url) > 10:
        return True
    
    # Проверяем полные URL
    youtube_patterns = [
        r'youtube\.com/@[\w-]+',
        r'youtube\.com/c/[\w-]+',
        r'youtube\.com/channel/UC[\w-]+',
        r'youtube\.com/user/[\w-]+'
    ]
    
    return any(re.search(pattern, url) for pattern in youtube_patterns)
