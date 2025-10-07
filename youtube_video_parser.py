import asyncio
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import yt_dlp

logger = logging.getLogger(__name__)


def validate_youtube_video_url(url: str) -> bool:
    """Проверить валидность URL YouTube видео"""
    if not url or len(url) < 10:
        return False
    
    youtube_patterns = [
        r'youtube\.com/watch\?v=[\w-]+',
        r'youtu\.be/[\w-]+',
        r'youtube\.com/shorts/[\w-]+',
    ]
    
    return any(re.search(pattern, url) for pattern in youtube_patterns)


def extract_video_id(url: str) -> Optional[str]:
    """Извлечь video ID из URL YouTube"""
    patterns = [
        r'youtube\.com/watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'youtube\.com/shorts/([\w-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


async def parse_youtube_video(url: str) -> Optional[Dict[str, Any]]:
    """
    Парсинг YouTube видео через yt-dlp
    Извлекает: video_id, title, channel_id, channel_name, upload_date, view_count, like_count, comment_count
    """
    try:
        logger.info(f"Парсинг YouTube видео: {url}")
        
        # Настройки yt-dlp с использованием куки из браузера
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'ignoreerrors': True,
            'socket_timeout': 30,  # Таймаут сокета
            'cookiesfrombrowser': ('chrome',),  # Используем куки из Chrome
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Пропускаем ненужные форматы
                }
            },
        }
        
        # Запускаем в отдельном потоке с таймаутом
        loop = asyncio.get_event_loop()
        
        try:
            video_info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: _extract_video_info(url, ydl_opts)
                ),
                timeout=60.0  # Максимум 60 секунд на парсинг
            )
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при парсинге видео: {url} (>60 сек)")
            return None
        
        if not video_info:
            logger.error(f"Не удалось получить информацию о видео: {url}")
            return None
        
        logger.info(f"✅ Видео распарсено: {video_info['title']}")
        logger.info(f"   Канал: {video_info['channel_name']} ({video_info['channel_id']})")
        logger.info(f"   Просмотры: {video_info['view_count']}, Лайки: {video_info['like_count']}, Комменты: {video_info['comment_count']}")
        logger.info(f"   Дата загрузки: {video_info['upload_date_str']}")
        
        return video_info
        
    except Exception as e:
        logger.error(f"Ошибка парсинга YouTube видео: {type(e).__name__} - {str(e)}")
        return None


def _extract_video_info(url: str, ydl_opts: dict) -> Optional[Dict[str, Any]]:
    """Вспомогательная функция для извлечения информации о видео"""
    info = None
    
    # Пробуем с куками
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None
    except Exception as e:
        # Если не удалось с куками, пробуем без них
        logger.warning(f"Ошибка с куками: {e}. Пробуем без куков...")
        try:
            ydl_opts_no_cookies = ydl_opts.copy()
            ydl_opts_no_cookies.pop('cookiesfrombrowser', None)
            
            with yt_dlp.YoutubeDL(ydl_opts_no_cookies) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
        except Exception as e2:
            logger.error(f"Не удалось получить информацию даже без куков: {e2}")
            return None
    
    # Извлекаем данные из полученной информации
    try:
        video_id = info.get('id')
        title = info.get('title', 'Без названия')
        channel_id = info.get('channel_id')
        channel_name = info.get('channel') or info.get('uploader')
        
        # Дата загрузки - используем timestamp для точного времени
        upload_datetime = None
        
        # Пробуем получить точную дату из timestamp
        timestamp = info.get('timestamp') or info.get('release_timestamp')
        if timestamp:
            try:
                upload_datetime = datetime.fromtimestamp(timestamp)
            except:
                pass
        
        # Если timestamp нет, используем upload_date (только дата без времени)
        if not upload_datetime:
            upload_date = info.get('upload_date')  # Формат: YYYYMMDD
            if upload_date:
                try:
                    upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                except:
                    pass
        
        # Статистика
        view_count = info.get('view_count', 0) or 0
        like_count = info.get('like_count', 0) or 0
        comment_count = info.get('comment_count', 0) or 0
        
        # Длительность
        duration = info.get('duration', 0)
        
        return {
            'video_id': video_id,
            'title': title,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'upload_date': upload_datetime,
            'upload_date_str': upload_datetime.strftime('%Y-%m-%d %H:%M:%S') if upload_datetime else 'Неизвестно',
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'duration': duration,
            'url': info.get('webpage_url', url)
        }
        
    except Exception as e:
        logger.error(f"Ошибка в _extract_video_info: {type(e).__name__} - {str(e)}")
        return None


def is_video_fresh(upload_date: datetime, hours: int = 24) -> bool:
    """Проверить, что видео загружено не позднее указанного количества часов назад"""
    if not upload_date:
        return False
    
    now = datetime.now()
    time_diff = now - upload_date
    
    return time_diff <= timedelta(hours=hours)
