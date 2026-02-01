"""yt-dlp wrapper for video downloading."""

import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

from utils.config import config_manager

logger = logging.getLogger(__name__)


# Error patterns ordered by specificity (most specific first)
ERROR_PATTERNS = [
    # Cookie extraction failures - actionable
    ('could not copy', 'Cannot access browser cookies. Close browser or use cookies.txt file in Settings.'),
    ('dpapi', 'Cannot decrypt browser cookies. Use cookies.txt file instead (see Settings).'),
    ('failed to decrypt', 'Cannot decrypt browser cookies. Use cookies.txt file instead (see Settings).'),
    
    # Bot detection - actionable
    ('sign in to confirm you\'re not a bot', 'YouTube requires authentication. Set up cookies in Settings.'),
    ('confirm you\'re not a bot', 'YouTube requires authentication. Set up cookies in Settings.'),
    
    # Age restriction - actionable (cookies can help)
    ('sign in to confirm your age', 'This video requires age verification. Set up cookies in Settings.'),
    ('age-restricted', 'This video is age-restricted. Set up cookies in Settings.'),
    ('age gate', 'This video is age-restricted. Set up cookies in Settings.'),
    
    # Login required - actionable (cookies can help)
    ('sign in to view', 'This video requires sign-in. Set up cookies in Settings.'),
    ('members only', 'This video is for channel members only.'),
    ('join this channel', 'This video is for channel members only.'),
    ('premium', 'This video requires a premium subscription.'),
    
    # Availability - not actionable
    ('video unavailable', 'This video is unavailable. It may have been removed or made private.'),
    ('private video', 'This video is private.'),
    ('removed by', 'This video has been removed.'),
    ('deleted video', 'This video has been deleted.'),
    ('copyright', 'This video was removed due to a copyright claim.'),
    
    # Geo-restriction - not actionable
    ('not available in your country', 'This video is not available in your region.'),
    ('geo', 'This video is geographically restricted.'),
    ('blocked in your country', 'This video is blocked in your region.'),
    
    # Live content
    ('live event will begin', 'This is an upcoming live stream. Try again when it starts.'),
    ('premieres in', 'This video will premiere later. Try again after it starts.'),
    
    # HTTP errors
    ('403', 'Access denied. Try importing browser cookies in Settings.'),
    ('404', 'Video not found. Check the URL.'),
    ('429', 'Too many requests. Please wait a moment and try again.'),
    ('503', 'Service temporarily unavailable. Try again later.'),
    
    # Network errors
    ('connection', 'Connection error. Check your internet connection.'),
    ('timeout', 'Connection timed out. Try again.'),
    ('network', 'Network error. Check your internet connection.'),
    ('ssl', 'Secure connection failed. Check your network settings.'),
    
    # Technical errors
    ('ffmpeg', 'FFmpeg is required but not found or failed.'),
    ('postprocessing', 'Failed to process the downloaded video.'),
    ('no video formats', 'No downloadable formats found for this video.'),
    ('unsupported url', 'This URL is not supported.'),
]


@dataclass
class VideoInfo:
    """Video metadata."""
    url: str
    title: str
    duration: int  # seconds
    thumbnail: Optional[str]
    uploader: Optional[str]
    extractor: str  # youtube, vimeo, etc.

    @property
    def duration_str(self) -> str:
        """Format duration as HH:MM:SS or MM:SS."""
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


# Quality presets mapping to yt-dlp format strings
QUALITY_PRESETS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "audio": "bestaudio/best",
}


def get_ffmpeg_path() -> Optional[str]:
    """Get FFmpeg path, handling PyInstaller bundling."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        base_path = sys._MEIPASS
    else:
        # Running as script - check project root
        base_path = Path(__file__).parent.parent.parent

    ffmpeg = Path(base_path) / 'ffmpeg.exe'
    if ffmpeg.exists():
        return str(ffmpeg.parent)

    return None  # Let yt-dlp find it in PATH


class Downloader:
    """Video downloader using yt-dlp."""

    def __init__(self):
        self.ffmpeg_location = get_ffmpeg_path()

    def _get_base_opts(self) -> dict:
        """Get base yt-dlp options."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'remote_components': ['ejs:github'],
            'concurrent_fragment_downloads': 4,
            # Fix BUG-01: Sanitize filenames for Windows compatibility
            # Handles invalid chars (?*"<>|:/\), reserved names (CON, PRN), path limits
            'windowsfilenames': True,
        }
        
        # Add cookies if configured (FEAT-01)
        # Priority: cookie file > browser extraction (file is more reliable)
        cookie_file = config_manager.get('cookie_file_path', '')
        cookie_browser = config_manager.get('cookie_browser', '')
        
        if cookie_file and os.path.exists(cookie_file):
            opts['cookiefile'] = cookie_file
        elif cookie_browser:
            opts['cookiesfrombrowser'] = (cookie_browser,)  # Tuple format required by yt-dlp
        
        if self.ffmpeg_location:
            opts['ffmpeg_location'] = self.ffmpeg_location
        return opts

    def get_info(self, url: str) -> VideoInfo:
        """Extract video information without downloading."""
        logger.info('Getting video info: %s', url[:80])
        opts = self._get_base_opts()

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)

                logger.info('Video info retrieved: %s (duration: %s)', info.get('title', 'Unknown')[:50], info.get('duration', 0))
                return VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail'),
                    uploader=info.get('uploader'),
                    extractor=info.get('extractor', 'unknown'),
                )
            except ExtractorError as e:
                logger.error('Extractor error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                logger.exception('Failed to get video info for %s', url[:50])
                raise DownloaderError(f"Failed to get video info: {e}")

    def download(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        progress_callback: Optional[Callable[[int, float, str], None]] = None,
    ) -> str:
        """
        Download video.

        Args:
            url: Video URL
            output_path: Directory to save to
            quality: Quality preset key
            progress_callback: Callback(percent, speed_mbps, status)

        Returns:
            Path to downloaded file
        """
        opts = self._get_base_opts()
        opts['format'] = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['best'])
        opts['overwrites'] = True

        # Filename template with quality
        if quality == 'audio':
            opts['outtmpl'] = os.path.join(output_path, '%(title)s [audio].%(ext)s')
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            opts['outtmpl'] = os.path.join(output_path, '%(title)s [%(height)sp].%(ext)s')
            opts['merge_output_format'] = 'mp4'

        downloaded_file = None
        last_logged_milestone = 0

        def progress_hook(d):
            nonlocal downloaded_file, last_logged_milestone

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed') or 0

                if total > 0:
                    percent = int(downloaded / total * 100)
                    speed_mbps = speed / 1_000_000  # Convert to MB/s
                    if progress_callback:
                        progress_callback(percent, speed_mbps, 'downloading')
                    
                    # Only log at milestones to avoid log spam
                    for milestone in (25, 50, 75, 100):
                        if percent >= milestone and last_logged_milestone < milestone:
                            logger.debug('Download progress: %d%% for %s', percent, url[:50])
                            last_logged_milestone = milestone
                            break

            elif d['status'] == 'finished':
                downloaded_file = d.get('filename')
                if progress_callback:
                    progress_callback(100, 0, 'processing')
                logger.debug('Download progress: 100%% for %s', url[:50])

        opts['progress_hooks'] = [progress_hook]
        logger.info('Starting download: %s (quality: %s)', url[:80], quality)

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ydl.download([url])
                if progress_callback:
                    progress_callback(100, 0, 'completed')
                logger.info('Download completed: %s', downloaded_file or output_path)
                return downloaded_file or output_path
            except DownloadError as e:
                logger.error('Download error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                logger.exception('Unexpected download error for %s', url[:50])
                raise DownloaderError(f"Download failed: {e}")

    def _translate_error(self, error: Exception) -> str:
        """Translate yt-dlp errors to user-friendly messages."""
        msg = str(error).lower()
        
        # Check against known patterns
        for pattern, friendly_msg in ERROR_PATTERNS:
            if pattern in msg:
                return friendly_msg
        
        # Fallback: Clean up the original message
        return self._clean_error_message(str(error))
    
    def _clean_error_message(self, msg: str) -> str:
        """Remove technical details and wiki links from error message."""
        # Remove GitHub/wiki URLs
        msg = re.sub(r'https?://[^\s]+', '', msg)
        # Remove "ERROR:" prefixes
        msg = re.sub(r'^ERROR:\s*', '', msg, flags=re.IGNORECASE)
        # Remove yt-dlp technical prefixes
        msg = re.sub(r'\[[\w\.-]+\]\s*', '', msg)
        # Collapse whitespace
        msg = re.sub(r'\s+', ' ', msg).strip()
        # Truncate if too long
        if len(msg) > 200:
            msg = msg[:197] + '...'
        return msg if msg else 'Download failed. Please try again.'


class DownloaderError(Exception):
    """Custom exception for download errors."""
    pass
